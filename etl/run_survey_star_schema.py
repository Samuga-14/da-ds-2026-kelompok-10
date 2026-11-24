"""
Load normalized survey staging data into the Toba survey star schema.

The existing dummy warehouse remains unchanged. This pipeline creates:
  data/tobakost_survey_warehouse.db
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
STAGING_PATH = BASE_DIR / "data" / "staging" / "survey_clean_v1.csv"
DB_PATH = BASE_DIR / "data" / "tobakost_survey_warehouse.db"


def build_survey_warehouse():
    if not STAGING_PATH.exists():
        raise FileNotFoundError(
            f"Staging data tidak ditemukan: {STAGING_PATH}. "
            "Jalankan python etl/normalize_survey.py terlebih dahulu."
        )

    df = pd.read_csv(STAGING_PATH)
    df = df.loc[df["accepted_for_analysis"].eq(1)].copy()
    if df.empty:
        raise ValueError("Tidak ada baris staging yang lolos validasi dasar.")

    df["id_kost"] = [f"KOST_{index:04d}" for index in range(1, len(df) + 1)]
    df["kode_unit_kos"] = [f"UNIT_{index:04d}" for index in range(1, len(df) + 1)]

    location_columns = ["kecamatan", "desa_kelurahan", "nama_kost"]
    if "tujuan_utama" in df.columns:
        location_columns.append("tujuan_utama")
    dim_location = df[location_columns].drop_duplicates().reset_index(drop=True)
    dim_location["id_lokasi"] = [f"LOK_{index:03d}" for index in range(1, len(dim_location) + 1)]

    specification_columns = [
        "luas_kamar_m2",
        "jumlah_lantai",
        "kategori_lantai",
        "tipe_kamar_mandi",
        "kelengkapan_kamar_mandi",
        "ac",
        "ada_dipan",
        "ada_kasur",
        "ada_lemari",
        "ada_meja_belajar",
        "ada_tv",
        "ada_cermin",
        "ada_kulkas_pribadi",
    ]
    specification_columns = [col for col in specification_columns if col in df.columns]
    dim_specification = df[specification_columns].drop_duplicates().reset_index(drop=True)
    dim_specification["id_spesifikasi"] = [
        f"SPK_{index:03d}" for index in range(1, len(dim_specification) + 1)
    ]

    regulation_columns = [
        "kategori_penghuni",
        "status_penyewa",
        "keamanan_kos",
        "lahan_parkir",
        "aturan_jam_malam",
        "kapasitas_kamar",
        "skema_listrik",
        "listrik_termasuk",
        "wifi",
        "sumber_air",
        "fasilitas_dapur",
        "fasilitas_cuci_jemur",
    ]
    dim_regulation = df[regulation_columns].drop_duplicates().reset_index(drop=True)
    dim_regulation["id_aturan"] = [
        f"ATR_{index:03d}" for index in range(1, len(dim_regulation) + 1)
    ]

    contract_columns = ["periode_sewa", "sewa_tahunan"]
    dim_contract = df[contract_columns].drop_duplicates().reset_index(drop=True)
    dim_contract["id_kontrak"] = [
        f"KTK_{index:03d}" for index in range(1, len(dim_contract) + 1)
    ]

    fact = df.merge(dim_location, on=location_columns, how="left")
    fact = fact.merge(dim_specification, on=specification_columns, how="left")
    fact = fact.merge(dim_regulation, on=regulation_columns, how="left")
    fact = fact.merge(dim_contract, on=contract_columns, how="left")

    candidate_fact_columns = [
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
        "klasifikasi_jarak_kampus_sekolah_tempatkerja",
        "klasifikasi_jarak_pasar_minimarket",
        "klasifikasi_jarak_fasilitas_kesehatan",
        "klasifikasi_jarak_tempat_ibadah",
        "klasifikasi_jarak_laundry",
        "klasifikasi_jarak_pusat_kota",
        "klasifikasi_jarak_jalan_raya",
        "area_tempat_makan",
        "biaya_tambahan_rp",
        "exact_duplicate",
        "duplicate_logis",
        "price_anomaly_iqr",
        "accepted_for_analysis",
        "model_ready",
    ]
    fact_columns = [col for col in candidate_fact_columns if col in fact.columns]
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
            s.luas_kamar_m2,
            s.jumlah_lantai,
            s.kategori_lantai,
            s.tipe_kamar_mandi,
            s.kelengkapan_kamar_mandi,
            s.ac,
            s.ada_dipan,
            s.ada_kasur,
            s.ada_lemari,
            s.ada_meja_belajar,
            s.ada_tv,
            s.ada_cermin,
            s.ada_kulkas_pribadi,
            a.kategori_penghuni,
            a.status_penyewa,
            a.keamanan_kos,
            a.lahan_parkir,
            a.aturan_jam_malam,
            a.kapasitas_kamar,
            a.skema_listrik,
            a.listrik_termasuk,
            a.wifi,
            a.sumber_air,
            a.fasilitas_dapur,
            a.fasilitas_cuci_jemur,
            k.periode_sewa,
            k.sewa_tahunan
        FROM fact_sewa_kos f
        JOIN dim_lokasi l ON f.id_lokasi = l.id_lokasi
        JOIN dim_spesifikasi_kamar s ON f.id_spesifikasi = s.id_spesifikasi
        JOIN dim_fasilitas_aturan a ON f.id_aturan = a.id_aturan
        JOIN dim_kontrak_sewa k ON f.id_kontrak = k.id_kontrak
        """)
        conn.commit()

    print("Warehouse survey dibuat:", DB_PATH)
    print("Fact rows:", len(fact_table))
    print("Model-ready rows:", int(fact_table["model_ready"].sum()))


if __name__ == "__main__":
    build_survey_warehouse()
