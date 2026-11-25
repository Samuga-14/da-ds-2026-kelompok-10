
"""Shared feature engineering and model-readiness checks for TobaKost ML."""

from __future__ import annotations

import numpy as np
import pandas as pd

# Target yang akan diprediksi oleh model
TARGET_COL = "harga_bulanan_norm"

# Fitur X yang digunakan oleh Linear Regression dan Ridge Regression
FEATURE_COLS = [
    "luas_kamar_m2",
    "jumlah_lantai",
    "km_dalam",
    "is_ac",
    "is_wifi",
    "ada_tv",
    "ada_meja_belajar",
    "parkir_mobil",
    "dapur_pribadi",
    "dapur_bersama",
    "keamanan_penjaga",
    "keamanan_cctv",
    "bebas_24jam",
    "listrik_termasuk",
    "jarak_ke_kampus_kantor_sekolah_terdekat_km",
    "jarak_ke_pasar_km",
    "jarak_krusial_km",
    "jarak_ke_jalan_raya_m",
    "is_tahunan",
    "skor_kelengkapan_fasilitas",
    "indeks_aksesibilitas_lokasi",
]

# Kolom sumber untuk membuat fitur kategorikal
MODEL_READY_SOURCE_COLS = [
    "tipe_kamar_mandi",
    "ac_non_ac",
    "wifi_non_wifi",
    "lahan_parkir",
    "dapur",
    "keamanan_kos",
    "aturan_jam_malam_masuk",
    "skema_biaya_listrik",
    "sewa_tahunan_bulanan",
]

# Kategori yang diperbolehkan berdasarkan data warehouse
MODEL_READY_ALLOWED_CATEGORIES = {
    "tipe_kamar_mandi": {"dalam", "luar"},
    "ac_non_ac": {"ac", "non-ac"},
    "wifi_non_wifi": {"wifi", "non-wifi"},
    "lahan_parkir": {
        "mobil & motor",
        "motor",
        "tidak ada",
    },
    "dapur": {"pribadi", "bersama", "tidak ada"},
    "keamanan_kos": {
        "penjaga & cctv",
        "cctv saja",
        "tidak ada",
    },
    "aturan_jam_malam_masuk": {
        "bebas 24 jam",
        "ada batas jam malam",
    },
    "skema_biaya_listrik": {
        "termasuk sewa",
        "token sendiri",
    },
    "sewa_tahunan_bulanan": {"tahunan", "bulanan"},
}

BINARY_FEATURE_COLS = [
    "km_dalam",
    "is_ac",
    "is_wifi",
    "ada_tv",
    "ada_meja_belajar",
    "parkir_mobil",
    "dapur_pribadi",
    "dapur_bersama",
    "keamanan_penjaga",
    "keamanan_cctv",
    "bebas_24jam",
    "listrik_termasuk",
    "is_tahunan",
]

NON_NEGATIVE_FEATURE_COLS = [
    "jarak_ke_kampus_kantor_sekolah_terdekat_km",
    "jarak_ke_pasar_km",
    "jarak_krusial_km",
    "jarak_ke_jalan_raya_m",
]


def add_model_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Mengubah fitur kategorikal menjadi numerik
    dan menghasilkan fitur turunan untuk model.
    """

    required = MODEL_READY_SOURCE_COLS

    missing = [
        column for column in required
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            "Kolom sumber feature engineering tidak tersedia: "
            + ", ".join(missing)
        )

    df = df.copy()

    # Mengubah kategori menjadi fitur binary
    df["km_dalam"] = (
        df["tipe_kamar_mandi"] == "dalam"
    ).astype(int)

    df["is_ac"] = (
        df["ac_non_ac"] == "ac"
    ).astype(int)

    df["is_wifi"] = (
        df["wifi_non_wifi"] == "wifi"
    ).astype(int)

    df["parkir_mobil"] = (
        df["lahan_parkir"] == "mobil & motor"
    ).astype(int)

    df["dapur_pribadi"] = (
        df["dapur"] == "pribadi"
    ).astype(int)

    df["dapur_bersama"] = (
        df["dapur"] == "bersama"
    ).astype(int)

    df["keamanan_penjaga"] = (
        df["keamanan_kos"] == "Penjaga & CCTV"
    ).astype(int)

    df["keamanan_cctv"] = (
        df["keamanan_kos"] == "CCTV Saja"
    ).astype(int)

    df["bebas_24jam"] = (
        df["aturan_jam_malam_masuk"] == "Bebas 24 Jam"
    ).astype(int)

    df["listrik_termasuk"] = (
        df["skema_biaya_listrik"] == "termasuk sewa"
    ).astype(int)

    df["is_tahunan"] = (
        df["sewa_tahunan_bulanan"] == "tahunan"
    ).astype(int)

    return add_derived_features(df)


def add_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Menghitung skor kelengkapan fasilitas
    dan indeks aksesibilitas lokasi.
    """

    df = df.copy()

    # Menghitung skor fasilitas
    df["skor_kelengkapan_fasilitas"] = (
        df["km_dalam"] * 2.5
        + df["is_ac"] * 3.5
        + df["is_wifi"] * 1.5
        + df["ada_tv"] * 0.5
        + df["ada_meja_belajar"] * 0.5
        + df["parkir_mobil"] * 0.5
        + df["dapur_pribadi"] * 0.5
        + df["keamanan_penjaga"] * 0.5
    ).round(1)

    # Menghitung indeks aksesibilitas lokasi
    df["indeks_aksesibilitas_lokasi"] = (
        (1.0 / (
            1.0 + df["jarak_ke_kampus_kantor_sekolah_terdekat_km"]
        )) * 35
        + (1.0 / (
            1.0 + df["jarak_ke_pasar_km"]
        )) * 25
        + (1.0 / (
            1.0 + df["jarak_krusial_km"]
        )) * 20
        + (1.0 / (
            1.0 + df["jarak_ke_jalan_raya_m"] / 100.0
        )) * 20
    ).round(1)

    return df


def _model_ready_flag(series: pd.Series) -> pd.Series:
    """Membaca berbagai format nilai status model_ready."""

    if pd.api.types.is_bool_dtype(series):
        return series.fillna(False).astype(bool)

    numeric = pd.to_numeric(series, errors="coerce")
    numeric_values = numeric.eq(1)

    text = (
        series.astype("string")
        .str.strip()
        .str.lower()
    )

    accepted_true = {
        "true",
        "1",
        "yes",
        "y",
        "ready",
        "model_ready",
        "siap",
    }

    text_values = text.isin(accepted_true)

    return (
        numeric_values | text_values
    ).fillna(False)


def build_model_ready_mask(
    df: pd.DataFrame,
    target_col: str = TARGET_COL,
) -> pd.Series:
    """
    Memeriksa kelayakan baris data sebelum training.

    Jika kolom model_ready tersedia, nilainya tetap dihormati.
    Jika belum tersedia, kelayakan ditentukan berdasarkan
    validitas fitur dan target.
    """

    required = list(FEATURE_COLS) + [target_col]

    missing = [
        column for column in required
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            "Kolom wajib model_ready tidak tersedia: "
            + ", ".join(missing)
        )

    # Konversi seluruh fitur dan target menjadi numerik
    numeric = df[required].apply(
        pd.to_numeric,
        errors="coerce"
    )

    values = numeric.to_numpy(dtype=float)

    ready = pd.Series(
        np.isfinite(values).all(axis=1),
        index=df.index,
        dtype=bool,
    )

    # Memastikan kategori sumber tidak kosong atau tidak dikenal
    source_cols = [
        column for column in MODEL_READY_SOURCE_COLS
        if column in df.columns
    ]

    if source_cols:
        source_valid = df[source_cols].notna().all(axis=1)

        for column in source_cols:
            normalized = (
                df[column]
                .astype("string")
                .str.strip()
                .str.lower()
            )

            source_valid &= normalized.isin(
                MODEL_READY_ALLOWED_CATEGORIES[column]
            )

        ready &= source_valid.fillna(False)

    # Jika status model_ready sudah tersedia dari warehouse,
    # hanya baris dengan status siap yang digunakan
    if "model_ready" in df.columns:
        ready &= _model_ready_flag(df["model_ready"])

    # Target harga harus lebih besar dari nol
    ready &= numeric[target_col].gt(0)

    # Luas kamar harus positif
    ready &= numeric["luas_kamar_m2"].gt(0)

    # Jumlah lantai harus bilangan bulat minimal 1
    ready &= numeric["jumlah_lantai"].ge(1)

    ready &= np.isclose(
        numeric["jumlah_lantai"].to_numpy(dtype=float),
        np.round(
            numeric["jumlah_lantai"].to_numpy(dtype=float)
        ),
    )

    # Fitur binary hanya boleh bernilai 0 atau 1
    for column in BINARY_FEATURE_COLS:
        ready &= numeric[column].isin([0, 1])

    # Jarak tidak boleh negatif
    for column in NON_NEGATIVE_FEATURE_COLS:
        ready &= numeric[column].ge(0)

    # Memvalidasi rentang skor fasilitas
    ready &= numeric[
        "skor_kelengkapan_fasilitas"
    ].between(0, 10)

    # Memvalidasi indeks aksesibilitas
    ready &= numeric[
        "indeks_aksesibilitas_lokasi"
    ].between(0, 100)

    return ready.fillna(False).rename("model_ready")


def build_feature_frame(df: pd.DataFrame) -> pd.DataFrame:
    """
    Mengambil fitur X sesuai urutan kolom standar model.
    """

    missing = [
        column for column in FEATURE_COLS
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            "Fitur model tidak tersedia: "
            + ", ".join(missing)
        )

    features = df.loc[:, FEATURE_COLS].apply(
        pd.to_numeric,
        errors="coerce"
    )

    if not np.isfinite(
        features.to_numpy(dtype=float)
    ).all():
        raise ValueError(
            "Feature frame masih mengandung missing value "
            "atau nilai non-finite."
        )

    return features
