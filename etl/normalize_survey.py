"""
Normalize the 328-row Toba kos survey without changing the raw CSV.

The script creates a staging CSV and a JSON quality report. It does not silently
drop outliers or logical duplicates.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
RAW_PATH = BASE_DIR / "data" / "raw" / "data_fix.csv"
STAGING_DIR = BASE_DIR / "data" / "staging"
REPORT_DIR = BASE_DIR / "data" / "quality"
STAGING_PATH = STAGING_DIR / "survey_clean_v1.csv"
REPORT_PATH = REPORT_DIR / "survey_quality_v1.json"


def find_column(df: pd.DataFrame, *phrases: str) -> str:
    for column in df.columns:
        normalized = " ".join(str(column).lower().split())
        if all(phrase.lower() in normalized for phrase in phrases):
            return column
    raise KeyError(f"Kolom tidak ditemukan: {phrases}")


def numeric_value(value):
    if pd.isna(value):
        return np.nan
    text = str(value).strip()
    text = text.replace(" ", "")
    match = re.search(r"-?\d+(?:[.,]\d+)*", text)
    if not match:
        return np.nan

    number = match.group(0)
    if "," in number and "." in number:
        number = number.replace(".", "").replace(",", ".")
    elif "," in number:
        number = number.replace(".", "")
        number = number.replace(",", ".")
    elif re.search(r"\.\d{3}$", number):
        number = number.replace(".", "")
    return float(number)


def text_value(value):
    if pd.isna(value):
        return ""
    return " ".join(str(value).strip().split())


def normalize_survey(raw_path: Path = RAW_PATH):
    df = pd.read_csv(raw_path)
    raw_count = len(df)

    name = find_column(df, "nama kos")
    kecamatan = find_column(df, "kecamatan")
    desa = find_column(df, "desa")
    category = find_column(df, "kategori penghuni")
    occupant_status = find_column(df, "status penyewa")
    campus_distance = find_column(df, "jarak", "kampus")
    market_distance = find_column(df, "jarak", "pasar")
    health_distance = find_column(df, "jarak", "kesehatan")
    worship_distance = find_column(df, "jarak", "ibadah")
    eating_area = find_column(df, "area", "tempat makan")
    road_distance = find_column(df, "jalan raya")
    center_distance = find_column(df, "pusat kota")
    laundry_distance = find_column(df, "laundry")
    room_floor = find_column(df, "lantai")
    room_area = find_column(df, "luas kamar")
    bedroom_facilities = find_column(df, "fasilitas didalam kamar")
    ac = find_column(df, "ada pendingin")
    bathroom_type = find_column(df, "tipe kamar mandi")
    bathroom_facilities = find_column(df, "kelengkapan isi")
    electricity = find_column(df, "skema biaya listrik")
    period = find_column(df, "periode pembayaran")
    rent = find_column(df, "nominal harga sewa")
    security = find_column(df, "keamanan kos")
    parking = find_column(df, "lahan parkir")
    night_rule = find_column(df, "aturan jam malam")
    capacity = find_column(df, "kapasitas penghuni")
    wifi = find_column(df, "fasilitas internet")
    kitchen = find_column(df, "dapur")
    laundry = find_column(df, "cuci pakaian")
    water = find_column(df, "sumber air")
    validity = find_column(df, "harga sewa tersebut masih berlaku")
    included_cost = find_column(df, "harga sewa kos sudah termasuk")
    has_extra_cost = find_column(df, "biaya tambahan")
    extra_cost = find_column(df, "total biaya tambahan")
    renter_age = find_column(df, "usia")
    renter_year = find_column(df, "sejak tahun")

    canonical = pd.DataFrame()
    canonical["nama_kost"] = df[name].map(text_value).str.strip()
    canonical["kecamatan"] = df[kecamatan].map(text_value).str.strip().str.title()
    canonical["desa_kelurahan"] = df[desa].map(text_value).str.strip().str.title()
    canonical["kategori_penghuni"] = df[category].map(text_value).str.strip().str.title()
    canonical["status_penyewa"] = df[occupant_status].map(text_value).str.strip()
    canonical["status_penyewa"] = canonical["status_penyewa"].str.lower().replace({
        "siswa": "pelajar",
        "siswa sma": "pelajar",
        "pelajar sma": "pelajar",
        "siswa/pelajar": "pelajar",
    }).replace("", "tidak disebutkan").str.title()
    canonical["usia_mulai_menyewa"] = df[renter_age].map(numeric_value)
    canonical["tahun_mulai_menyewa"] = df[renter_year].map(numeric_value)

    numeric_columns = {
        "jarak_kampus_sekolah_tempatkerja_m": campus_distance,
        "jarak_pasar_minimarket_m": market_distance,
        "jarak_fasilitas_kesehatan_m": health_distance,
        "jarak_tempat_ibadah_m": worship_distance,
        "jarak_laundry_m": laundry_distance,
        "jarak_pusat_kota_m": center_distance,
        "jarak_jalan_raya_m": road_distance,
        "luas_kamar_m2": room_area,
        "harga_sewa": rent,
    }
    for output, source in numeric_columns.items():
        canonical[output] = df[source].map(numeric_value)

    canonical["jumlah_lantai"] = df[room_floor].map(numeric_value)
    canonical["tipe_kamar_mandi"] = df[bathroom_type].map(text_value).str.strip().str.lower()
    canonical["kelengkapan_kamar_mandi"] = df[bathroom_facilities].map(text_value)
    canonical["kloset_duduk"] = canonical["kelengkapan_kamar_mandi"].str.contains("duduk", case=False, na=False).astype(int)
    canonical["kloset_jongkok"] = canonical["kelengkapan_kamar_mandi"].str.contains("jongkok", case=False, na=False).astype(int)
    canonical["ada_shower"] = canonical["kelengkapan_kamar_mandi"].str.contains("shower", case=False, na=False).astype(int)
    canonical["ada_water_heater"] = canonical["kelengkapan_kamar_mandi"].str.contains("water heater", case=False, na=False).astype(int)

    facilities = df[bedroom_facilities].map(text_value)
    canonical["fasilitas_kamar_detail"] = facilities
    for name_output, phrase in {
        "ada_dipan": "dipan",
        "ada_kasur": "kasur",
        "ada_lemari": "lemari",
        "ada_meja_belajar": "meja",
        "ada_tv": "televisi",
        "ada_cermin": "cermin",
        "ada_kulkas_pribadi": "kulkas",
    }.items():
        canonical[name_output] = facilities.str.contains(phrase, case=False, na=False).astype(int)

    canonical["ac"] = df[ac].map(text_value).str.contains("Ada", case=False, na=False).astype(int)
    canonical["skema_listrik"] = df[electricity].map(text_value)
    canonical["listrik_termasuk"] = canonical["skema_listrik"].str.contains("termasuk", case=False, na=False).astype(int)
    canonical["periode_sewa"] = df[period].map(text_value).str.strip().str.lower()
    canonical["sewa_tahunan"] = canonical["periode_sewa"].eq("per tahun").astype(int)
    canonical["harga_bulanan_norm"] = np.where(
        canonical["sewa_tahunan"].eq(1),
        canonical["harga_sewa"] / 12,
        canonical["harga_sewa"],
    )
    canonical["harga_bulanan_norm"] = canonical["harga_bulanan_norm"].round()

    canonical["keamanan_kos"] = df[security].map(text_value)
    canonical["lahan_parkir"] = df[parking].map(text_value)
    canonical["aturan_jam_malam"] = df[night_rule].map(text_value)
    canonical["kapasitas_kamar"] = df[capacity].map(text_value)
    canonical["wifi"] = df[wifi].map(text_value).str.strip().str.lower()
    canonical["sumber_air"] = df[water].map(text_value)
    canonical["fasilitas_dapur"] = df[kitchen].map(text_value)
    canonical["fasilitas_cuci_jemur"] = df[laundry].map(text_value)
    canonical["area_tempat_makan"] = df[eating_area].map(text_value)
    canonical["status_harga"] = df[validity].map(text_value)
    canonical["harga_masih_berlaku"] = canonical["status_harga"].str.startswith("Ya", na=False).astype(int)
    canonical["kos_aktif"] = (
        ~canonical["status_harga"].str.contains("tidak beroperasi", case=False, na=False)
    ).astype(int)

    canonical["biaya_sewa_sudah_mencakup"] = df[included_cost].map(text_value)
    canonical["ada_biaya_tambahan"] = df[has_extra_cost].map(text_value)
    canonical["biaya_tambahan_rp"] = df[extra_cost].map(numeric_value)
    canonical["biaya_tambahan_rp"] = canonical["biaya_tambahan_rp"].fillna(0)

    canonical["exact_duplicate"] = df.duplicated(keep=False).astype(int)
    duplicate_key = [
        "nama_kost", "kecamatan", "desa_kelurahan", "jumlah_lantai",
        "luas_kamar_m2", "periode_sewa", "harga_sewa",
    ]
    canonical["duplicate_logis"] = canonical.duplicated(subset=duplicate_key, keep=False).astype(int)

    valid_numeric = (
        canonical["harga_bulanan_norm"].ge(100_000)
        & canonical["harga_bulanan_norm"].le(20_000_000)
        & canonical["luas_kamar_m2"].gt(0)
        & canonical["luas_kamar_m2"].le(100)
    )
    q1 = canonical.loc[valid_numeric, "harga_bulanan_norm"].quantile(0.25)
    q3 = canonical.loc[valid_numeric, "harga_bulanan_norm"].quantile(0.75)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    canonical["price_anomaly_iqr"] = (
        ~canonical["harga_bulanan_norm"].between(lower, upper)
    ).astype(int)

    rejection_reasons = []
    for index, row in canonical.iterrows():
        reasons = []
        if not valid_numeric.loc[index]:
            reasons.append("harga atau luas kamar tidak valid")
        if row["kos_aktif"] != 1:
            reasons.append("kos tidak beroperasi")
        if row["exact_duplicate"] == 1:
            reasons.append("exact duplicate")
        rejection_reasons.append("; ".join(reasons))
    canonical["rejection_reason"] = rejection_reasons
    canonical["accepted_for_analysis"] = canonical["rejection_reason"].eq("").astype(int)
    canonical["model_ready"] = (
        canonical["accepted_for_analysis"].eq(1)
        & canonical["harga_masih_berlaku"].eq(1)
        & canonical["price_anomaly_iqr"].eq(0)
        & canonical["duplicate_logis"].eq(0)
    ).astype(int)

    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    canonical.to_csv(STAGING_PATH, index=False)

    report = {
        "raw_path": str(raw_path),
        "raw_rows": raw_count,
        "raw_columns": len(df.columns),
        "staging_path": str(STAGING_PATH),
        "staging_rows": len(canonical),
        "exact_duplicates": int(canonical["exact_duplicate"].sum()),
        "logical_duplicate_rows": int(canonical["duplicate_logis"].sum()),
        "accepted_for_analysis": int(canonical["accepted_for_analysis"].sum()),
        "model_ready": int(canonical["model_ready"].sum()),
        "price_anomaly_iqr": int(canonical["price_anomaly_iqr"].sum()),
        "price_iqr_bounds": {"lower": round(float(lower), 2), "upper": round(float(upper), 2)},
        "missing_cells_by_column": {
            column: int(count)
            for column, count in canonical.isna().sum().sort_values(ascending=False).items()
            if count
        },
        "rejection_counts": canonical["rejection_reason"].value_counts().to_dict(),
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return canonical, report


if __name__ == "__main__":
    normalize_survey()
