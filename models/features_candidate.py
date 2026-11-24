"""Fitur kandidat dan split data untuk baseline model prediksi tarif kos (Issue #16).

File ini sengaja diberi nama ``features_candidate.py`` supaya TIDAK menimpa
``models/features.py`` yang dipakai API dan model .pkl yang sudah ada. Setelah tim
sepakat dengan daftar fitur, gabungkan ke ``features.py`` dan latih ulang model (Issue #18).

Alur pemakaian:
    df = load_warehouse("data/tobakost_survey_warehouse.db")
    df = select_model_ready(add_binary_flags(df))
    split = make_split(df)                 # train 80% / test 20%, random_state=42
"""
from __future__ import annotations

import sqlite3
import warnings
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

TARGET = "harga_bulanan_norm"
ID_COLUMN = "id_kost"
RANDOM_STATE = 42
TEST_SIZE = 0.20

# ---------------------------------------------------------------- kelompok fitur
NUMERIC_FEATURES = [
    "luas_kamar_m2",
    "jumlah_lantai",
    "jarak_ke_kampus_kantor_sekolah_terdekat_km",
    "jarak_ke_pasar_km",
    "jarak_krusial_km",            # jarak ke RS / puskesmas / klinik
    "jarak_laundry_m",
    "jarak_ibadah_m",
    "jarak_pusat_kota_m",
    "jarak_ke_jalan_raya_m",
]

BINARY_FEATURES = [
    "is_ac", "km_dalam", "is_wifi", "parkir_mobil",
    "dapur_pribadi", "dapur_bersama",
    "keamanan_penjaga", "keamanan_cctv",          # keamanan_cctv = "CCTV Saja"
    "bebas_24jam", "listrik_termasuk",
    "ada_lemari", "ada_kasur", "ada_tv", "ada_meja_belajar",
    "kloset_duduk", "ada_shower", "ada_water_heater",
]

CATEGORICAL_FEATURES = [
    "kecamatan", "kategori_penghuni", "sumber_air_utama",
    "kapasitas_kamar", "area_tempat_makan",
]

# Variabel kontrol skema pembayaran. Pengaruhnya besar (lihat notebook), jadi tim perlu memutuskan
# apakah dipakai sebagai kontrol atau model dilatih hanya pada kontrak bulanan.
CONTRACT_FEATURES = ["is_tahunan"]

FEATURE_GROUPS = {
    "ukuran dan lantai": ["luas_kamar_m2", "jumlah_lantai"],
    "aksesibilitas (jarak)": [c for c in NUMERIC_FEATURES if c.startswith("jarak_")],
    "fasilitas": BINARY_FEATURES,
    "wilayah dan profil kos": CATEGORICAL_FEATURES,
    "kontrol kontrak": CONTRACT_FEATURES,
}

# Kolom yang TIDAK boleh menjadi fitur beserta alasannya.
EXCLUDED_COLUMNS = {
    "harga_sewa": "kebocoran target: harga_bulanan_norm diturunkan dari kolom ini",
    "harga_bulanan_norm": "ini target",
    "pred_rf": "hasil prediksi model (kebocoran)", "pred_ridge": "hasil prediksi model (kebocoran)",
    "pred_gb": "hasil prediksi model (kebocoran)", "pred_ols": "hasil prediksi model (kebocoran)",
    "selisih_rp": "diturunkan dari target (kebocoran)", "selisih_persen": "diturunkan dari target (kebocoran)",
    "abs_error": "diturunkan dari target (kebocoran)", "status_kewajaran": "diturunkan dari target (kebocoran)",
    "skor_kelengkapan_fasilitas": "kombinasi linear persis dari fitur fasilitas (redundan, R2 = 1,0)",
    "indeks_aksesibilitas_lokasi": "turunan dari fitur jarak (redundan, ganda menghitung)",
    "tahun_mulai_sewa": "bukan spesifikasi kos; tiap kos berbeda sehingga bukan tren waktu",
    "latitude": "identitas lokasi; sudah terwakili kecamatan dan jarak", "longitude": "idem latitude",
    "id_kost": "pengenal", "kode_unit_kos": "pengenal", "nama_kost": "pengenal", "source_url": "pengenal",
}

_DIM_TABLES = {
    "dim_lokasi": "id_lokasi",
    "dim_spesifikasi_kamar": "id_spesifikasi",
    "dim_fasilitas_aturan": "id_aturan",
    "dim_kontrak_sewa": "id_kontrak",
}


# ---------------------------------------------------------------- data
def load_warehouse(db_path: str | Path) -> pd.DataFrame:
    """Gabungkan tabel fakta dan empat tabel dimensi menjadi satu baris per kos."""
    with sqlite3.connect(str(db_path)) as con:
        fact = pd.read_sql("SELECT * FROM fact_sewa_kos", con)
        out = fact
        for table, key in _DIM_TABLES.items():
            out = out.merge(pd.read_sql(f"SELECT * FROM {table}", con), on=key, how="left", validate="m:1")
    if len(out) != len(fact):
        raise ValueError(f"Join mengubah jumlah baris: {len(fact)} -> {len(out)}")
    return out


def add_binary_flags(df: pd.DataFrame) -> pd.DataFrame:
    """Turunkan fitur biner dari kolom teks dimensi bila belum ada."""
    df = df.copy()
    rules = {
        "is_ac": lambda d: d["ac_non_ac"].str.lower().eq("ac"),
        "km_dalam": lambda d: d["tipe_kamar_mandi"].str.lower().eq("dalam"),
        "is_wifi": lambda d: d["wifi_non_wifi"].str.lower().eq("wifi"),
        "parkir_mobil": lambda d: d["lahan_parkir"].str.lower().str.contains("mobil"),
        "dapur_pribadi": lambda d: d["dapur"].str.lower().eq("pribadi"),
        "dapur_bersama": lambda d: d["dapur"].str.lower().eq("bersama"),
        "keamanan_penjaga": lambda d: d["keamanan_kos"].str.lower().str.contains("penjaga"),
        "keamanan_cctv": lambda d: d["keamanan_kos"].str.lower().eq("cctv saja"),
        "bebas_24jam": lambda d: d["aturan_jam_malam_masuk"].str.lower().str.contains("bebas"),
        "listrik_termasuk": lambda d: d["skema_biaya_listrik"].str.lower().str.contains("termasuk"),
    }
    for col, rule in rules.items():
        if col not in df.columns:
            df[col] = rule(df).astype(int)
    if "is_tahunan" not in df.columns and "sewa_tahunan_bulanan" in df.columns:
        df["is_tahunan"] = df["sewa_tahunan_bulanan"].str.lower().eq("tahunan").astype(int)
    return df


def select_model_ready(df: pd.DataFrame) -> pd.DataFrame:
    """Baris siap model: pakai kolom model_ready bila ada; jika tidak,
    pakai aturan: target terisi dan > 0, semua fitur lengkap."""
    if "model_ready" in df.columns:
        keep = df["model_ready"].astype(str).str.lower().isin(["1", "true", "ya", "yes"])
    else:
        needed = [TARGET] + NUMERIC_FEATURES + CATEGORICAL_FEATURES + CONTRACT_FEATURES
        keep = df[needed].notna().all(axis=1) & (df[TARGET] > 0)
        print("Kolom model_ready tidak ada; memakai aturan: target > 0 dan fitur lengkap.")
    print(f"Baris siap model: {int(keep.sum())} dari {len(df)}")
    return df[keep].copy()


# ---------------------------------------------------------------- fitur
def check_no_leakage(columns) -> None:
    bad = [c for c in columns if c in EXCLUDED_COLUMNS]
    if bad:
        raise ValueError("Kolom terlarang sebagai fitur: " + ", ".join(f"{c} ({EXCLUDED_COLUMNS[c]})" for c in bad))


def build_features(df: pd.DataFrame, include_contract: bool = True, columns: list[str] | None = None) -> pd.DataFrame:
    """Bangun matriks fitur. ``columns`` dipakai saat prediksi agar urutan kolom sama dengan saat latih."""
    parts = [
        df[NUMERIC_FEATURES].astype(float),
        df[BINARY_FEATURES].astype(int),
        pd.get_dummies(df[CATEGORICAL_FEATURES], drop_first=True, dtype=int),
    ]
    if include_contract:
        parts.append(df[CONTRACT_FEATURES].astype(int))
    X = pd.concat(parts, axis=1)
    if columns is not None:
        X = X.reindex(columns=columns, fill_value=0)
    if X.isna().any().any():
        raise ValueError("Fitur mengandung nilai kosong: " + ", ".join(X.columns[X.isna().any()]))
    check_no_leakage(X.columns)
    return X


# ---------------------------------------------------------------- split
def make_split(df: pd.DataFrame, include_contract: bool = True) -> dict:
    """Split 80/20 yang reproducible (random_state tetap)."""
    X = build_features(df, include_contract=include_contract)
    y = df[TARGET].astype(float)
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, shuffle=True)
    return {"X_train": X_tr, "X_test": X_te, "y_train": y_tr, "y_test": y_te,
            "ids_train": df.loc[X_tr.index, ID_COLUMN].tolist(), "ids_test": df.loc[X_te.index, ID_COLUMN].tolist(),
            "columns": list(X.columns)}


def save_split_ids(split: dict, path: str | Path) -> None:
    """Simpan id kos per bagian split agar semua anggota memakai pembagian yang sama."""
    rows = [(i, "train") for i in split["ids_train"]] + [(i, "test") for i in split["ids_test"]]
    pd.DataFrame(rows, columns=[ID_COLUMN, "bagian"]).sort_values(ID_COLUMN).to_csv(path, index=False)