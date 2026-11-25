"""Shared feature engineering for training and model inference."""

import numpy as np
import pandas as pd


FEATURE_COLS = [
    "luas_kamar_m2", "jumlah_lantai", "km_dalam", "is_ac", "is_wifi",
    "ada_tv", "ada_meja_belajar", "parkir_mobil", "dapur_pribadi", "dapur_bersama",
    "keamanan_penjaga", "keamanan_cctv", "bebas_24jam", "listrik_termasuk",
    "jarak_ke_kampus_kantor_sekolah_terdekat_km", "jarak_ke_pasar_km",
    "jarak_krusial_km", "jarak_ke_jalan_raya_m", "is_tahunan",
    "skor_kelengkapan_fasilitas", "indeks_aksesibilitas_lokasi"
]


def add_model_features(df):
    """Apply the same binary and derived features used by the ETL pipeline (supports both survey and legacy column names)."""
    df = df.copy()
    df["km_dalam"] = (df["tipe_kamar_mandi"].astype(str).str.lower() == "dalam").astype(int)
    if "ac" in df.columns:
        df["is_ac"] = pd.to_numeric(df["ac"], errors="coerce").fillna(0).astype(int)
    else:
        df["is_ac"] = (df["ac_non_ac"].astype(str).str.lower() == "ac").astype(int)

    if "wifi_non_wifi" in df.columns:
        df["is_wifi"] = (df["wifi_non_wifi"].astype(str).str.lower() == "wifi").astype(int)
    else:
        df["is_wifi"] = (df.get("wifi", pd.Series(dtype=str)).astype(str).str.lower() == "ada").astype(int)

    df["parkir_mobil"] = df["lahan_parkir"].astype(str).str.lower().str.contains("mobil", na=False).astype(int)

    if "dapur" in df.columns:
        df["dapur_pribadi"] = (df["dapur"].astype(str).str.lower() == "pribadi").astype(int)
        df["dapur_bersama"] = (df["dapur"].astype(str).str.lower() == "bersama").astype(int)
    else:
        dapur_col = df.get("fasilitas_dapur", pd.Series(dtype=str)).astype(str).str.lower()
        df["dapur_pribadi"] = dapur_col.str.contains("pribadi", na=False).astype(int)
        df["dapur_bersama"] = dapur_col.str.contains("bersama", na=False).astype(int)

    sec_col = df["keamanan_kos"].astype(str).str.lower()
    df["keamanan_penjaga"] = sec_col.str.contains("penjaga|satpam", na=False).astype(int)
    df["keamanan_cctv"] = sec_col.isin(["cctv", "cctv saja"]).astype(int)

    night_col = df.get("aturan_jam_malam_masuk", df.get("aturan_jam_malam", pd.Series(dtype=str))).astype(str).str.lower()
    df["bebas_24jam"] = night_col.str.contains("bebas", na=False).astype(int)

    if "listrik_termasuk" in df.columns:
        df["listrik_termasuk"] = pd.to_numeric(df["listrik_termasuk"], errors="coerce").fillna(0).astype(int)
    else:
        df["listrik_termasuk"] = (df["skema_biaya_listrik"].astype(str).str.lower() == "termasuk sewa").astype(int)

    if "is_tahunan" in df.columns:
        df["is_tahunan"] = pd.to_numeric(df["is_tahunan"], errors="coerce").fillna(0).astype(int)
    elif "sewa_tahunan" in df.columns:
        df["is_tahunan"] = pd.to_numeric(df["sewa_tahunan"], errors="coerce").fillna(0).astype(int)
    else:
        df["is_tahunan"] = (df["sewa_tahunan_bulanan"].astype(str).str.lower() == "tahunan").astype(int)

    if "jarak_ke_kampus_kantor_sekolah_terdekat_km" not in df.columns and "jarak_kampus_sekolah_tempatkerja_m" in df.columns:
        df["jarak_ke_kampus_kantor_sekolah_terdekat_km"] = (df["jarak_kampus_sekolah_tempatkerja_m"] / 1000.0).round(3)
    if "jarak_ke_pasar_km" not in df.columns and "jarak_pasar_minimarket_m" in df.columns:
        df["jarak_ke_pasar_km"] = (df["jarak_pasar_minimarket_m"] / 1000.0).round(3)
    if "jarak_krusial_km" not in df.columns and "jarak_fasilitas_kesehatan_m" in df.columns:
        df["jarak_krusial_km"] = (df["jarak_fasilitas_kesehatan_m"] / 1000.0).round(3)
    if "jarak_ke_jalan_raya_m" not in df.columns and "jarak_jalan_raya_m" in df.columns:
        df["jarak_ke_jalan_raya_m"] = df["jarak_jalan_raya_m"].round(0)

    return add_derived_features(df)


def add_derived_features(df):
    """Calculate the shared facility score and location-accessibility index."""
    df = df.copy()
    df["skor_kelengkapan_fasilitas"] = (
        df["km_dalam"] * 2.5 +
        df["is_ac"] * 3.5 +
        df["is_wifi"] * 1.5 +
        df["ada_tv"] * 0.5 +
        df["ada_meja_belajar"] * 0.5 +
        df["parkir_mobil"] * 0.5 +
        df["dapur_pribadi"] * 0.5 +
        df["keamanan_penjaga"] * 0.5
    ).round(1)

    df["indeks_aksesibilitas_lokasi"] = (
        (1.0 / (1.0 + df["jarak_ke_kampus_kantor_sekolah_terdekat_km"])) * 35 +
        (1.0 / (1.0 + df["jarak_ke_pasar_km"])) * 25 +
        (1.0 / (1.0 + df["jarak_krusial_km"])) * 20 +
        (1.0 / (1.0 + df["jarak_ke_jalan_raya_m"] / 100.0)) * 20
    ).round(1)
    return df


def build_feature_frame(df):
    """Return model input in the canonical training and inference column order."""
    missing = [column for column in FEATURE_COLS if column not in df.columns]
    if missing:
        raise ValueError(f"Fitur model tidak tersedia: {', '.join(missing)}")
    return df.loc[:, FEATURE_COLS]
