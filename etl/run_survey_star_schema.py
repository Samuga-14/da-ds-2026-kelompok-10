"""
Load normalized survey staging data (`data/staging/survey_clean_v1.csv`, 928 rows)
into the unified Toba survey star schema warehouse:
  - `data/tobakost_survey_warehouse.db` (canonical survey warehouse, 923 fact rows)
  - `data/tobakost_warehouse.db` (active runtime warehouse consumed by API & ML)

Both databases share the exact same star schema (`dim_lokasi`, `dim_spesifikasi_kamar`,
`dim_fasilitas_aturan`, `dim_kontrak_sewa`, `fact_sewa_kos`, and `vw_mart_kos_lengkap`)
with both survey-native columns (e.g. `jarak_*_m`, `klasifikasi_jarak_*`, `kategori_lantai`,
`ac`, `wifi`, `model_ready`) and API/ML compatibility columns (`ac_non_ac`, `wifi_non_wifi`,
`jarak_ke_*_km`, `skor_kelengkapan_fasilitas`, `indeks_aksesibilitas_lokasi`, `latitude`,
`longitude`) so that dashboard, analytics service, and ML models read from a single
source of truth.
"""

from __future__ import annotations

import shutil
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
STAGING_PATH = BASE_DIR / "data" / "staging" / "survey_clean_v1.csv"
DB_PATH = BASE_DIR / "data" / "tobakost_survey_warehouse.db"
ACTIVE_DB_PATH = BASE_DIR / "data" / "tobakost_warehouse.db"
NORMALIZE_SCRIPT = BASE_DIR / "etl" / "normalize_survey.py"

# Centroid coordinates for the 16 districts (kecamatan) of Toba Regency
KECAMATAN_COORDS = {
    "Balige": (2.3335, 99.0625),
    "Laguboti": (2.3835, 99.1465),
    "Porsea": (2.4431, 99.1558),
    "Ajibata": (2.6580, 98.9365),
    "Silaen": (2.3980, 99.2050),
    "Habinsaran": (2.2910, 99.3180),
    "Parmaksian": (2.4630, 99.1740),
    "Borbor": (2.2380, 99.2900),
    "Lumban Julu": (2.5690, 99.0350),
    "Siantar Narumonda": (2.4260, 99.1770),
    "Sigumpar": (2.3990, 99.1580),
    "Tampahan": (2.3180, 99.0120),
    "Uluan": (2.4780, 99.1240),
    "Nassau": (2.2850, 99.4100),
    "Bonatua Lunasi": (2.4950, 99.1450),
    "Pintu Pohan Meranti": (2.5120, 99.2580),
}


def _map_furniture_tier(row) -> str:
    if int(row.get("ada_kulkas_pribadi", 0)) == 1 or int(row.get("ada_tv", 0)) == 1:
        return "Eksekutif (Lengkap + TV & Kulkas Mini)"
    if int(row.get("ada_cermin", 0)) == 1:
        return "Lengkap (Dipan, Kasur, Lemari, Meja, Cermin)"
    if int(row.get("ada_meja_belajar", 0)) == 1:
        return "Menengah (Dipan, Kasur, Lemari, Meja & Kursi)"
    if int(row.get("ada_kasur", 0)) == 1:
        return "Dasar (Kasur & Lemari)"
    return "Kamar Kosong (Tanpa Furnitur)"


def _assign_coordinates(df: pd.DataFrame) -> tuple[list[float], list[float]]:
    rng = np.random.default_rng(42)
    lats, lons = [], []
    for kec in df["kecamatan"]:
        base_lat, base_lon = KECAMATAN_COORDS.get(str(kec), (2.3500, 99.1200))
        lats.append(round(float(base_lat + rng.normal(0, 0.0045)), 6))
        lons.append(round(float(base_lon + rng.normal(0, 0.0045)), 6))
    return lats, lons


def build_survey_warehouse():
    if not STAGING_PATH.exists():
        from normalize_survey import normalize_survey
        normalize_survey()

    df = pd.read_csv(STAGING_PATH)
    df = df.loc[df["accepted_for_analysis"].eq(1)].copy().reset_index(drop=True)
    if df.empty:
        raise ValueError("Tidak ada baris staging yang lolos validasi dasar.")

    df["id_kost"] = [f"KOST_{index:04d}" for index in range(1, len(df) + 1)]
    df["kode_unit_kos"] = [f"UNIT_{index:04d}" for index in range(1, len(df) + 1)]

    # Compatibility & derived columns for API, Frontend, and ML
    df["nama_tempat_krusial"] = df.get("tujuan_utama", "Kampus / Kantor")
    df["ac_non_ac"] = np.where(df["ac"].eq(1), "ac", "non-ac")
    df["fasilitas"] = df.apply(_map_furniture_tier, axis=1)

    df["km_dalam"] = (df["tipe_kamar_mandi"].str.lower() == "dalam").astype(int)
    df["is_ac"] = df["ac"].astype(int)
    df["wifi_non_wifi"] = np.where(df["wifi"].str.lower() == "ada", "wifi", "non-wifi")
    df["is_wifi"] = (df["wifi_non_wifi"] == "wifi").astype(int)
    df["sumber_air_utama"] = df["sumber_air"]
    df["fasilitas_dapur_kulkas"] = df["fasilitas_dapur"]
    df["dapur"] = np.where(
        df["fasilitas_dapur"].str.contains("Pribadi", case=False, na=False),
        "pribadi",
        np.where(
            df["fasilitas_dapur"].str.contains("Bersama", case=False, na=False),
            "bersama",
            "tidak ada",
        ),
    )
    df["aturan_jam_malam_masuk"] = df["aturan_jam_malam"]
    df["skema_biaya_listrik"] = np.where(
        df["listrik_termasuk"].eq(1), "termasuk sewa", "token sendiri"
    )
    df["sewa_tahunan_bulanan"] = np.where(df["sewa_tahunan"].eq(1), "tahunan", "bulanan")
    df["is_tahunan"] = df["sewa_tahunan"].astype(int)
    df["tahun_mulai_sewa"] = "2026"

    # Distance conversions (meters remain canonical, kilometers added for backward compatibility)
    df["jarak_ke_kampus_kantor_sekolah_terdekat_km"] = (
        df["jarak_kampus_sekolah_tempatkerja_m"] / 1000.0
    ).round(3)
    df["jarak_ke_pasar_km"] = (df["jarak_pasar_minimarket_m"] / 1000.0).round(3)
    df["jarak_krusial_km"] = (df["jarak_fasilitas_kesehatan_m"] / 1000.0).round(3)
    df["jarak_ibadah_m"] = df["jarak_tempat_ibadah_m"].round(0).astype(int)
    df["jarak_ke_jalan_raya_m"] = df["jarak_jalan_raya_m"].round(0).astype(int)
    df["jarak_laundry_m"] = df["jarak_laundry_m"].round(0).astype(int)
    df["jarak_pusat_kota_m"] = df["jarak_pusat_kota_m"].round(0).astype(int)

    parkir_mobil = df["lahan_parkir"].str.contains("Mobil", case=False, na=False).astype(int)
    dapur_pribadi = (df["dapur"] == "pribadi").astype(int)
    keamanan_penjaga = df["keamanan_kos"].str.contains("Penjaga", case=False, na=False).astype(int)

    df["skor_kelengkapan_fasilitas"] = (
        df["km_dalam"] * 2.5
        + df["is_ac"] * 3.5
        + df["is_wifi"] * 1.5
        + df["ada_tv"] * 0.5
        + df["ada_meja_belajar"] * 0.5
        + parkir_mobil * 0.5
        + dapur_pribadi * 0.5
        + keamanan_penjaga * 0.5
    ).round(1)
    df["jenis_kos"] = np.where(
        df["skor_kelengkapan_fasilitas"] >= 5.5, "eksekutif", "ekonomi"
    )
    df["indeks_aksesibilitas_lokasi"] = (
        (1.0 / (1.0 + df["jarak_ke_kampus_kantor_sekolah_terdekat_km"])) * 35
        + (1.0 / (1.0 + df["jarak_ke_pasar_km"])) * 25
        + (1.0 / (1.0 + df["jarak_krusial_km"])) * 20
        + (1.0 / (1.0 + df["jarak_ke_jalan_raya_m"] / 100.0)) * 20
    ).round(1)

    lats, lons = _assign_coordinates(df)
    df["latitude"] = lats
    df["longitude"] = lons
    df["source_url"] = "https://forms.gle/SurveiKosKabupatenTobaITDel"

    # 1. dim_lokasi
    location_columns = [
        "kecamatan",
        "desa_kelurahan",
        "nama_kost",
        "tujuan_utama",
        "nama_tempat_krusial",
        "area_tempat_makan",
    ]
    dim_location = df[location_columns].drop_duplicates().reset_index(drop=True)
    dim_location["id_lokasi"] = [f"LOK_{index:03d}" for index in range(1, len(dim_location) + 1)]
    dim_location = dim_location[["id_lokasi"] + location_columns]

    # 2. dim_spesifikasi_kamar
    specification_columns = [
        "luas_kamar_m2",
        "jumlah_lantai",
        "kategori_lantai",
        "tipe_kamar_mandi",
        "kelengkapan_kamar_mandi",
        "ac",
        "ac_non_ac",
        "fasilitas",
        "fasilitas_kamar_detail",
        "ada_dipan",
        "ada_kasur",
        "ada_lemari",
        "ada_meja_belajar",
        "ada_tv",
        "ada_cermin",
        "ada_kulkas_pribadi",
        "kloset_duduk",
        "kloset_jongkok",
        "ada_shower",
        "ada_water_heater",
        "jenis_kos",
    ]
    dim_specification = df[specification_columns].drop_duplicates().reset_index(drop=True)
    dim_specification["id_spesifikasi"] = [
        f"SPK_{index:03d}" for index in range(1, len(dim_specification) + 1)
    ]
    dim_specification = dim_specification[["id_spesifikasi"] + specification_columns]

    # 3. dim_fasilitas_aturan
    regulation_columns = [
        "kategori_penghuni",
        "status_penyewa",
        "sumber_air",
        "sumber_air_utama",
        "wifi",
        "wifi_non_wifi",
        "fasilitas_dapur",
        "fasilitas_dapur_kulkas",
        "dapur",
        "fasilitas_cuci_jemur",
        "lahan_parkir",
        "keamanan_kos",
        "aturan_jam_malam",
        "aturan_jam_malam_masuk",
        "kapasitas_kamar",
        "skema_listrik",
        "skema_biaya_listrik",
        "listrik_termasuk",
    ]
    dim_regulation = df[regulation_columns].drop_duplicates().reset_index(drop=True)
    dim_regulation["id_aturan"] = [
        f"ATR_{index:03d}" for index in range(1, len(dim_regulation) + 1)
    ]
    dim_regulation = dim_regulation[["id_aturan"] + regulation_columns]

    # 4. dim_kontrak_sewa
    contract_columns = [
        "periode_sewa",
        "sewa_tahunan",
        "sewa_tahunan_bulanan",
        "is_tahunan",
        "tahun_mulai_sewa",
    ]
    dim_contract = df[contract_columns].drop_duplicates().reset_index(drop=True)
    dim_contract["id_kontrak"] = [
        f"KTK_{index:03d}" for index in range(1, len(dim_contract) + 1)
    ]
    dim_contract["faktor_konversi_bulanan"] = np.where(dim_contract["is_tahunan"] == 1, 12, 1)
    dim_contract = dim_contract[["id_kontrak"] + contract_columns + ["faktor_konversi_bulanan"]]

    fact = df.merge(dim_location, on=location_columns, how="left")
    fact = fact.merge(dim_specification, on=specification_columns, how="left")
    fact = fact.merge(dim_regulation, on=regulation_columns, how="left")
    fact = fact.merge(dim_contract, on=contract_columns, how="left")

    fact_columns = [
        "id_kost",
        "kode_unit_kos",
        "nama_kost",
        "id_lokasi",
        "id_spesifikasi",
        "id_aturan",
        "id_kontrak",
        "harga_sewa",
        "harga_bulanan_norm",
        "status_harga",
        "harga_masih_berlaku",
        "kos_aktif",
        "jarak_kampus_sekolah_tempatkerja_m",
        "jarak_pasar_minimarket_m",
        "jarak_fasilitas_kesehatan_m",
        "jarak_tempat_ibadah_m",
        "jarak_laundry_m",
        "jarak_pusat_kota_m",
        "jarak_jalan_raya_m",
        "jarak_ke_kampus_kantor_sekolah_terdekat_km",
        "jarak_ke_pasar_km",
        "jarak_krusial_km",
        "jarak_ibadah_m",
        "jarak_ke_jalan_raya_m",
        "klasifikasi_jarak_kampus_sekolah_tempatkerja",
        "klasifikasi_jarak_pasar_minimarket",
        "klasifikasi_jarak_fasilitas_kesehatan",
        "klasifikasi_jarak_tempat_ibadah",
        "klasifikasi_jarak_laundry",
        "klasifikasi_jarak_pusat_kota",
        "klasifikasi_jarak_jalan_raya",
        "area_tempat_makan",
        "biaya_tambahan_rp",
        "skor_kelengkapan_fasilitas",
        "indeks_aksesibilitas_lokasi",
        "latitude",
        "longitude",
        "source_url",
        "exact_duplicate",
        "duplicate_logis",
        "price_anomaly_iqr",
        "accepted_for_analysis",
        "model_ready",
    ]
    fact_table = fact[fact_columns].copy()

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()

    with sqlite3.connect(DB_PATH) as conn:
        dim_location.to_sql("dim_lokasi", conn, index=False, if_exists="replace")
        dim_specification.to_sql("dim_spesifikasi_kamar", conn, index=False, if_exists="replace")
        dim_regulation.to_sql("dim_fasilitas_aturan", conn, index=False, if_exists="replace")
        dim_contract.to_sql("dim_kontrak_sewa", conn, index=False, if_exists="replace")
        fact_table.to_sql("fact_sewa_kos", conn, index=False, if_exists="replace")

        conn.execute("""
        CREATE VIEW vw_mart_kos_lengkap AS
        SELECT
            f.*,
            l.kecamatan,
            l.desa_kelurahan,
            l.tujuan_utama,
            l.nama_tempat_krusial,
            s.luas_kamar_m2,
            s.jumlah_lantai,
            s.kategori_lantai,
            s.tipe_kamar_mandi,
            s.kelengkapan_kamar_mandi,
            s.ac,
            s.ac_non_ac,
            s.fasilitas,
            s.fasilitas_kamar_detail,
            s.ada_dipan,
            s.ada_kasur,
            s.ada_lemari,
            s.ada_meja_belajar,
            s.ada_tv,
            s.ada_cermin,
            s.ada_kulkas_pribadi,
            s.kloset_duduk,
            s.kloset_jongkok,
            s.ada_shower,
            s.ada_water_heater,
            s.jenis_kos,
            a.kategori_penghuni,
            a.status_penyewa,
            a.sumber_air,
            a.sumber_air_utama,
            a.wifi,
            a.wifi_non_wifi,
            a.fasilitas_dapur,
            a.fasilitas_dapur_kulkas,
            a.dapur,
            a.fasilitas_cuci_jemur,
            a.lahan_parkir,
            a.keamanan_kos,
            a.aturan_jam_malam,
            a.aturan_jam_malam_masuk,
            a.kapasitas_kamar,
            a.skema_listrik,
            a.skema_biaya_listrik,
            a.listrik_termasuk,
            k.periode_sewa,
            k.sewa_tahunan,
            k.sewa_tahunan_bulanan,
            k.is_tahunan,
            k.tahun_mulai_sewa
        FROM fact_sewa_kos f
        JOIN dim_lokasi l ON f.id_lokasi = l.id_lokasi
        JOIN dim_spesifikasi_kamar s ON f.id_spesifikasi = s.id_spesifikasi
        JOIN dim_fasilitas_aturan a ON f.id_aturan = a.id_aturan
        JOIN dim_kontrak_sewa k ON f.id_kontrak = k.id_kontrak
        """)
        conn.commit()

    # Synchronize active warehouse DB so API and ML read the exact same 923-row survey warehouse
    shutil.copy2(DB_PATH, ACTIVE_DB_PATH)

    print("Warehouse survey dibuat:", DB_PATH)
    print("Warehouse aktif disinkronkan:", ACTIVE_DB_PATH)
    print("Fact rows:", len(fact_table))
    print("Model-ready rows:", int(fact_table["model_ready"].sum()))


if __name__ == "__main__":
    build_survey_warehouse()
