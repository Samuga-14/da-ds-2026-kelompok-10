"""
TobaKost Analytics & ML — Backend Server (Arsitektur Paket A)
Stack: Python built-in HTTP REST API + SQLite Star Schema Data Warehouse + Pre-trained ML Models (.pkl)
Frontend: HTML5 + Tailwind CSS + Chart.js + Leaflet.js (frontend/index.html)

Cara Menjalankan:
1. Klik tombol Run Python File di VS Code, ATAU
2. Ketik di terminal: python server.py
Server akan otomatis berjalan di http://localhost:8000 dan membuka browser.
"""
import os
import sys
import json
import logging
import math
import pickle
import sqlite3
import subprocess
import webbrowser
from http import HTTPStatus
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs

import numpy as np
import pandas as pd
import sklearn

from models.features import FEATURE_COLS, add_derived_features, add_model_features, build_feature_frame
from services.analytics_service import (
    FACILITY_FILTERS,
    enrich_price_analysis,
    feature_importance,
    get_price_summary,
)
from services.database import connect, connection, ensure_readable_object, validate
from server_config import (
    BASE_DIR,
    DB_PATH,
    ETL_SCRIPT_PATH,
    FRONTEND_HTML_PATH,
    HOST,
    ADMIN_API_KEY,
    MODEL_PKL_PATH,
    PORT,
    TRAIN_SCRIPT_PATH,
)
LOGGER = logging.getLogger("tobakost")
MODEL_BUNDLE = None
MODEL_DIR = os.path.join(BASE_DIR, "models")
REGISTRY_MANIFEST_PATH = os.path.join(MODEL_DIR, "registry", "model_manifest.json")
MANIFEST_REQUIRED_KEYS = ("model_artifact", "features", "best_algorithm", "sklearn_version")


class RequestValidationError(ValueError):
    """Raised when an API request contains invalid user input."""


class ModelUnavailableError(RuntimeError):
    """Raised when the model artifact cannot be loaded safely."""


def ensure_database():
    """Ensure the SQLite warehouse exists without retraining models implicitly."""
    if not os.path.exists(DB_PATH):
        print("[INIT] Membangun SQLite Star Schema Data Warehouse...")
        subprocess.run([sys.executable, ETL_SCRIPT_PATH], check=True, cwd=BASE_DIR)


def read_model_manifest():
    """Baca models/registry/model_manifest.json: penunjuk model terbaik yang aktif."""
    if not os.path.exists(REGISTRY_MANIFEST_PATH):
        raise ModelUnavailableError(
            "Manifest model tidak ditemukan di models/registry/. Jalankan `python models/train_models.py` dari folder proyek."
        )
    try:
        with open(REGISTRY_MANIFEST_PATH, "r", encoding="utf-8") as f:
            manifest = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        raise ModelUnavailableError(
            "Manifest model rusak atau tidak bisa dibaca. Jalankan `python models/train_models.py`."
        ) from exc
    if not isinstance(manifest, dict):
        raise ModelUnavailableError("Format manifest model tidak valid; latih ulang dengan models/train_models.py.")
    missing = [key for key in MANIFEST_REQUIRED_KEYS if key not in manifest]
    if missing:
        raise ModelUnavailableError(f"Manifest model tidak lengkap, kunci hilang: {', '.join(missing)}.")
    return manifest


def resolve_model_artifact(manifest):
    """Ubah model_artifact di manifest menjadi path file; wajib berada di dalam folder models/."""
    artifact_path = os.path.abspath(os.path.join(BASE_DIR, str(manifest["model_artifact"])))
    models_root = os.path.abspath(MODEL_DIR)
    if os.path.commonpath([artifact_path, models_root]) != models_root:
        raise ModelUnavailableError("Lokasi model pada manifest berada di luar folder models/.")
    if not os.path.exists(artifact_path):
        raise ModelUnavailableError(
            f"File model {manifest['model_artifact']} tidak ditemukan. Jalankan `python models/train_models.py` untuk melatih dan menyimpan model."
        )
    return artifact_path


def load_model_bundle():
    global MODEL_BUNDLE
    ensure_database()
    if MODEL_BUNDLE is not None:
        return MODEL_BUNDLE

    manifest = read_model_manifest()
    if manifest["features"] != FEATURE_COLS:
        raise ModelUnavailableError(
            "Daftar fitur pada manifest tidak sesuai dengan fitur API; latih ulang model dengan models/train_models.py."
        )
    artifact_path = resolve_model_artifact(manifest)
    try:
        with open(artifact_path, "rb") as f:
            bundle = pickle.load(f)
    except Exception as exc:
        LOGGER.exception("Gagal memuat bundle model dari %s", artifact_path)
        raise ModelUnavailableError(
            "File model tidak kompatibel atau rusak. Jalankan `python models/train_models.py` dengan dependensi dari requirements.txt."
        ) from exc

    if not isinstance(bundle, dict):
        raise ModelUnavailableError("Format bundle model tidak valid; latih ulang dengan models/train_models.py.")
    artifact_version = bundle.get("sklearn_version")
    if artifact_version != sklearn.__version__:
        raise ModelUnavailableError(
            f"Model dibuat dengan scikit-learn {artifact_version or 'versi tidak tercatat'}, "
            f"tetapi runtime menggunakan {sklearn.__version__}. Jalankan `python models/train_models.py`."
        )
    if bundle.get("features") != FEATURE_COLS:
        raise ModelUnavailableError("Urutan fitur model tidak sesuai dengan fitur API; latih ulang model.")
    if bundle.get("features") != manifest["features"] or bundle.get("best_algorithm") != manifest["best_algorithm"]:
        raise ModelUnavailableError("Manifest tidak cocok dengan isi file model; latih ulang dengan models/train_models.py.")
    expected_models = {
        "Linear Regression (Baseline)",
        "Ridge Regression (L2 Tuned)",
        "Random Forest Regressor (Tuned)",
        "Gradient Boosting / XGBoost (Tuned)"
    }
    if set(bundle.get("all_models", {})) != expected_models:
        raise ModelUnavailableError("Bundle tidak memuat keempat model yang didukung.")
    if set(bundle.get("metrics", {})) != expected_models:
        raise ModelUnavailableError("Metrik model tidak lengkap atau tidak konsisten dengan bundle.")
    MODEL_BUNDLE = bundle
    return MODEL_BUNDLE


def _validate_database():
    ensure_database()
    return validate()


def _json_safe(value):
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, np.generic):
        return _json_safe(value.item())
    if value is pd.NA or value is pd.NaT:
        return None
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def _build_survey_eda_payload():
    base_dir = Path(BASE_DIR)
    staging_path = base_dir / "data" / "staging" / "survey_clean_v1.csv"
    if not staging_path.exists():
        return None

    df = pd.read_csv(staging_path)
    analysis = df.loc[df["accepted_for_analysis"].eq(1)].copy()
    prices = pd.to_numeric(analysis["harga_bulanan_norm"], errors="coerce").dropna()
    areas = pd.to_numeric(analysis["luas_kamar_m2"], errors="coerce").dropna()

    def median_rows(column):
        result = (
            analysis.groupby(column)["harga_bulanan_norm"]
            .agg(["count", "median"])
            .dropna()
            .reset_index()
            .sort_values("median")
        )
        return [
            {"label": str(row[column]), "median": float(row["median"]), "count": int(row["count"])}
            for _, row in result.iterrows()
        ]

    hist_prices = np.histogram(prices, bins=12)
    hist_areas = np.histogram(areas, bins=12)

    wifi_labels = analysis["wifi"].fillna("").astype(str).str.lower().str.contains("ada|tersedia")
    bathroom_labels = analysis["tipe_kamar_mandi"].fillna("").astype(str).str.lower().str.contains("dalam")
    facility_groups = {
        "AC": {
            "Ada AC": float(pd.to_numeric(analysis.loc[analysis["ac"].eq(1), "harga_bulanan_norm"], errors="coerce").median()) if (analysis["ac"].eq(1)).any() else None,
            "Tidak ada AC": float(pd.to_numeric(analysis.loc[analysis["ac"].eq(0), "harga_bulanan_norm"], errors="coerce").median()) if (analysis["ac"].eq(0)).any() else None,
        },
        "Wi-Fi": {
            "Ada Wi-Fi": float(pd.to_numeric(analysis.loc[wifi_labels, "harga_bulanan_norm"], errors="coerce").median()) if wifi_labels.any() else None,
            "Tanpa Wi-Fi": float(pd.to_numeric(analysis.loc[~wifi_labels, "harga_bulanan_norm"], errors="coerce").median()) if (~wifi_labels).any() else None,
        },
        "Kamar mandi": {
            "KM dalam": float(pd.to_numeric(analysis.loc[bathroom_labels, "harga_bulanan_norm"], errors="coerce").median()) if bathroom_labels.any() else None,
            "KM luar/lainnya": float(pd.to_numeric(analysis.loc[~bathroom_labels, "harga_bulanan_norm"], errors="coerce").median()) if (~bathroom_labels).any() else None,
        },
    }

    distance_columns = [column for column in analysis.columns if column.startswith("jarak_")]
    distance_corr = {}
    for column in distance_columns:
        pair = pd.DataFrame({
            "harga": pd.to_numeric(analysis["harga_bulanan_norm"], errors="coerce"),
            "jarak": pd.to_numeric(analysis[column], errors="coerce"),
        }).dropna()
        corr = float(pair.corr(method="spearman").iloc[0, 1]) if len(pair) >= 2 else 0.0
        distance_corr[column] = corr

    q1 = float(prices.quantile(0.25))
    q3 = float(prices.quantile(0.75))
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    missing = df.isna().sum().sort_values(ascending=False)
    missing = missing.drop(
        labels=[column for column in ["rejection_reason"] if column in missing.index],
        errors="ignore",
    )

    quality = {
        "raw_rows": int(len(df)),
        "accepted_rows": int(len(analysis)),
        "exact_duplicates": int(df["exact_duplicate"].sum()) if "exact_duplicate" in df else 0,
        "logical_duplicates": int(df["duplicate_logis"].sum()) if "duplicate_logis" in df else 0,
        "outliers": int(df["price_anomaly_iqr"].sum()) if "price_anomaly_iqr" in df else 0,
        "model_ready": int(df["model_ready"].sum()) if "model_ready" in df else 0,
        "missing": [{"column": str(column), "count": int(count)} for column, count in missing.items() if count > 0],
    }

    return {
        "quality": quality,
        "price_histogram": {
            "counts": hist_prices[0].tolist(),
            "edges": hist_prices[1].tolist(),
            "median": float(prices.median()),
        },
        "area_histogram": {
            "counts": hist_areas[0].tolist(),
            "edges": hist_areas[1].tolist(),
            "median": float(areas.median()),
        },
        "kecamatan": median_rows("kecamatan"),
        "kategori_penghuni": median_rows("kategori_penghuni"),
        "area_scatter": [
            {"area": float(row["luas_kamar_m2"]), "price": float(row["harga_bulanan_norm"])}
            for _, row in analysis[[ "luas_kamar_m2", "harga_bulanan_norm"]].dropna().iterrows()
        ],
        "facility_groups": facility_groups,
        "distance_corr": [
            {"label": column.replace("jarak_", "").replace("_m", "").replace("_", " ").title(), "correlation": corr}
            for column, corr in sorted(distance_corr.items(), key=lambda item: item[1])
        ],
        "outlier": {
            "prices": prices.tolist(),
            "lower": lower,
            "upper": upper,
        },
    }
def _read_summary_filters(query):
    """Read and validate the supported /api/summary query parameters."""
    with connection() as conn:
        districts = [
            row[0] for row in conn.execute(
                "SELECT DISTINCT kecamatan FROM dim_lokasi "
                "WHERE kecamatan IS NOT NULL ORDER BY kecamatan"
            ).fetchall()
        ]
        resident_categories = [
            row[0] for row in conn.execute(
                "SELECT DISTINCT kategori_penghuni FROM dim_fasilitas_aturan "
                "WHERE kategori_penghuni IS NOT NULL ORDER BY kategori_penghuni"
            ).fetchall()
        ]
        payment_periods = [
            row[0] for row in conn.execute(
                "SELECT DISTINCT sewa_tahunan_bulanan FROM dim_kontrak_sewa "
                "WHERE sewa_tahunan_bulanan IS NOT NULL "
                "ORDER BY sewa_tahunan_bulanan"
            ).fetchall()
        ]
        start_years = [
            row[0] for row in conn.execute(
                "SELECT DISTINCT tahun_mulai_sewa FROM dim_kontrak_sewa "
                "WHERE tahun_mulai_sewa IS NOT NULL ORDER BY tahun_mulai_sewa"
            ).fetchall()
        ]

    allowed_filters = {
        "kecamatan": (districts, districts),
        "kategori_penghuni": (
            [str(value).lower() for value in resident_categories],
            resident_categories,
        ),
        "sewa_tahunan_bulanan": (
            [str(value).lower() for value in payment_periods],
            payment_periods,
        ),
        "tahun_mulai_sewa": (start_years, start_years),
        "fasilitas": (list(FACILITY_FILTERS), list(FACILITY_FILTERS)),
    }

    filters = {}
    for name, (allowed_values, canonical_values) in allowed_filters.items():
        raw_values = query.get(name)
        if not raw_values:
            continue

        value = str(raw_values[0]).strip()
        if not value or value.upper() == "ALL":
            continue

        lookup = str(value).casefold()
        matched_index = None
        for index, allowed in enumerate(allowed_values):
            if str(allowed).casefold() == lookup:
                matched_index = index
                break

        if matched_index is None:
            choices = ", ".join(str(choice) for choice in canonical_values)
            raise RequestValidationError(
                f"Nilai '{value}' tidak valid untuk parameter '{name}'. "
                f"Pilihan tersedia: {choices}."
            )

        filters[name] = canonical_values[matched_index]

    for name in ("harga_min", "harga_max"):
        raw_values = query.get(name)
        if not raw_values:
            continue

        value = str(raw_values[0]).strip()
        if not value or value.upper() == "ALL":
            continue
        try:
            numeric_value = float(value)
        except ValueError as exc:
            raise RequestValidationError(
                f"Parameter '{name}' harus berupa angka finite dan tidak negatif."
            ) from exc
        if not math.isfinite(numeric_value) or numeric_value < 0:
            raise RequestValidationError(
                f"Parameter '{name}' harus berupa angka finite dan tidak negatif."
            )
        filters[name] = numeric_value

    if (
        filters.get("harga_min") is not None
        and filters.get("harga_max") is not None
        and filters["harga_min"] > filters["harga_max"]
    ):
        raise RequestValidationError(
            "Parameter 'harga_min' tidak boleh lebih besar daripada 'harga_max'."
        )

    return filters


def get_full_analytics_payload():
    """Mengambil seluruh data dari SQLite Star Schema + prediksi ML untuk Frontend."""
    bundle = load_model_bundle()
    all_models = bundle["all_models"]
    metrics = bundle["metrics"]

    with connection() as conn:
        df = pd.read_sql_query("SELECT * FROM vw_mart_kos_lengkap", conn)

        tables_info = {}
        for tbl in ["fact_sewa_kos", "dim_lokasi", "dim_spesifikasi_kamar", "dim_fasilitas_aturan", "dim_kontrak_sewa"]:
            cnt = conn.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
            sample_df = pd.read_sql_query(f"SELECT * FROM {tbl} LIMIT 25", conn)
            tables_info[tbl] = {
                "count": int(cnt),
                "columns": list(sample_df.columns),
                "rows": sample_df.to_dict(orient="records")
            }

    df = add_model_features(df)
    df = enrich_price_analysis(df, all_models)

    # Feature importance dari Random Forest & Gradient Boosting
    rf_model = all_models["Random Forest Regressor (Tuned)"]
    survey_eda = _build_survey_eda_payload()

    return _json_safe({
        "status": "ok",
        "architecture": "Paket A: Python REST API + SQLite Star Schema DW + HTML5/Tailwind/Chart.js/Leaflet",
        "total_records": int(len(df)),
        "best_algorithm": bundle["best_algorithm"],
        "model_version": bundle["sklearn_version"],
        "metrics": metrics,
        "feature_importance": feature_importance(rf_model),
        "star_schema": tables_info,
        "survey_eda": survey_eda,
        "records": df.to_dict(orient="records")
    })


def _read_numeric(payload, name, default, *, integer=False, binary=False):
    value = payload[name] if name in payload else default
    if value is None or value == "" or isinstance(value, bool):
        raise RequestValidationError(f"Fitur '{name}' harus berupa angka yang valid.")
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise RequestValidationError(f"Fitur '{name}' harus berupa angka yang valid.") from exc
    if not math.isfinite(numeric):
        raise RequestValidationError(f"Fitur '{name}' harus berupa angka finite.")
    if numeric < 0:
        raise RequestValidationError(f"Fitur '{name}' tidak boleh negatif.")
    if binary and numeric not in (0, 1):
        raise RequestValidationError(f"Fitur '{name}' hanya menerima nilai 0 atau 1.")
    if integer and not numeric.is_integer():
        raise RequestValidationError(f"Fitur '{name}' harus berupa bilangan bulat.")
    if name == "jumlah_lantai" and numeric < 1:
        raise RequestValidationError("Fitur 'jumlah_lantai' minimal bernilai 1.")
    if name == "luas_kamar_m2" and numeric == 0:
        raise RequestValidationError("Fitur 'luas_kamar_m2' harus lebih besar dari 0.")
    return int(numeric) if integer or binary else numeric


def predict_single_kos(payload):
    """Predict with each available model using the shared training feature order."""
    bundle = load_model_bundle()
    all_models = bundle["all_models"]
    metrics = bundle["metrics"]

    binary_defaults = {
        "km_dalam": 1, "is_ac": 0, "is_wifi": 1, "ada_tv": 0,
        "ada_meja_belajar": 1, "parkir_mobil": 0, "dapur_pribadi": 0,
        "dapur_bersama": 1, "keamanan_penjaga": 0, "keamanan_cctv": 1,
        "bebas_24jam": 1, "listrik_termasuk": 0, "is_tahunan": 0
    }
    values = {
        "luas_kamar_m2": _read_numeric(payload, "luas_kamar_m2", 12),
        "jumlah_lantai": _read_numeric(payload, "jumlah_lantai", 1, integer=True),
        **{
            name: _read_numeric(payload, name, default, binary=True)
            for name, default in binary_defaults.items()
        },
        "jarak_ke_kampus_kantor_sekolah_terdekat_km": _read_numeric(
            payload, "jarak_ke_kampus_kantor_sekolah_terdekat_km", 0.8
        ),
        "jarak_ke_pasar_km": _read_numeric(payload, "jarak_ke_pasar_km", 1.0),
        "jarak_krusial_km": _read_numeric(payload, "jarak_krusial_km", 1.5),
        "jarak_ke_jalan_raya_m": _read_numeric(payload, "jarak_ke_jalan_raya_m", 100)
    }

    row_df = add_derived_features(pd.DataFrame([values]))
    skor_fas = float(row_df.iloc[0]["skor_kelengkapan_fasilitas"])
    indeks_aks = float(row_df.iloc[0]["indeks_aksesibilitas_lokasi"])
    row_df = build_feature_frame(row_df)

    selected_algo = payload.get("algorithm", bundle["best_algorithm"])
    if not isinstance(selected_algo, str) or selected_algo not in all_models:
        raise RequestValidationError("Algoritma tidak dikenal. Pilih salah satu algoritma yang tersedia.")

    predictions = {}
    for name, model in all_models.items():
        try:
            output = np.asarray(model.predict(row_df)).reshape(-1)
            if output.size != 1 or not np.isfinite(output[0]):
                raise ValueError("Model tidak menghasilkan satu prediksi numerik finite.")
            predictions[name] = int(round(float(output[0])))
        except Exception as exc:
            LOGGER.exception("Prediksi model gagal: %s", name)
            predictions[name] = {"status": "error", "message": str(exc)}

    selected_result = predictions[selected_algo]
    if isinstance(selected_result, dict):
        return {
            "status": "partial",
            "selected_algorithm": selected_algo,
            "predicted_monthly_rp": None,
            "predicted_yearly_rp": None,
            "range_min_rp": None,
            "range_max_rp": None,
            "mae_rp": None,
            "skor_kelengkapan_fasilitas": skor_fas,
            "indeks_aksesibilitas_lokasi": indeks_aks,
            "best_algorithm": bundle["best_algorithm"],
            "all_predictions": predictions
        }

    mae_val = int(metrics[selected_algo]["MAE"])
    return {
        "status": "ok" if all(not isinstance(prediction, dict) for prediction in predictions.values()) else "partial",
        "selected_algorithm": selected_algo,
        "predicted_monthly_rp": selected_result,
        "predicted_yearly_rp": selected_result * 12,
        "range_min_rp": selected_result - mae_val,
        "range_max_rp": selected_result + mae_val,
        "mae_rp": mae_val,
        "skor_kelengkapan_fasilitas": skor_fas,
        "indeks_aksesibilitas_lokasi": indeks_aks,
        "best_algorithm": bundle["best_algorithm"],
        "all_predictions": predictions
    }


def insert_new_kos_to_dw(payload):
    """Menyimpan unit kos baru langsung ke tabel fact_sewa_kos di SQLite Data Warehouse."""
    ensure_database()
    conn = connect()
    cur = conn.cursor()

    total_now = cur.execute("SELECT COUNT(*) FROM fact_sewa_kos").fetchone()[0]
    new_id = f"TOBA_{total_now + 1:03d}"
    nama_kost = str(payload.get("nama_kost", f"Kost Baru Toba {total_now + 1}")).strip()
    kecamatan = str(payload.get("kecamatan", "Laguboti")).strip()
    desa = str(payload.get("desa_kelurahan", "Sitoluama")).strip()

    # Cari id_lokasi yang cocok di dim_lokasi atau ambil default
    lok_row = cur.execute(
        "SELECT id_lokasi FROM dim_lokasi WHERE kecamatan = ? LIMIT 1", (kecamatan,)
    ).fetchone()
    id_lokasi = lok_row[0] if lok_row else "LOK_001"

    tipe_km = "dalam" if int(payload.get("km_dalam", 1)) == 1 else "luar"
    ac_str = "ac" if int(payload.get("is_ac", 0)) == 1 else "non-ac"
    spk_row = cur.execute(
        "SELECT id_spesifikasi FROM dim_spesifikasi_kamar WHERE tipe_kamar_mandi = ? AND ac_non_ac = ? LIMIT 1",
        (tipe_km, ac_str)
    ).fetchone()
    id_spesifikasi = spk_row[0] if spk_row else "SPK_001"

    wifi_str = "wifi" if int(payload.get("is_wifi", 1)) == 1 else "non-wifi"
    atr_row = cur.execute(
        "SELECT id_aturan FROM dim_fasilitas_aturan WHERE wifi_non_wifi = ? LIMIT 1", (wifi_str,)
    ).fetchone()
    id_aturan = atr_row[0] if atr_row else "ATR_001"

    id_kontrak = "KTK_01"
    harga_bulanan = int(payload.get("harga_bulanan_norm", 700000))
    jarak_kampus = float(payload.get("jarak_ke_kampus_kantor_sekolah_terdekat_km", 0.8))
    jarak_pasar = float(payload.get("jarak_ke_pasar_km", 1.0))
    jarak_rs = float(payload.get("jarak_krusial_km", 1.5))
    jarak_jalan = int(payload.get("jarak_ke_jalan_raya_m", 100))

    skor_fas = round(int(payload.get("km_dalam", 1)) * 2.5 + int(payload.get("is_ac", 0)) * 3.5 + int(payload.get("is_wifi", 1)) * 1.5 + 1.5, 1)
    indeks_aks = round((1.0 / (1.0 + jarak_kampus)) * 35 + (1.0 / (1.0 + jarak_pasar)) * 25 + 30.0, 1)

    cur.execute("""
        INSERT INTO fact_sewa_kos (
            id_kost, kode_unit_kos, nama_kost, id_lokasi, id_spesifikasi, id_aturan, id_kontrak,
            harga_sewa, harga_bulanan_norm,
            jarak_ke_kampus_kantor_sekolah_terdekat_km, jarak_ke_pasar_km,
            jarak_krusial_km, jarak_laundry_m, jarak_ibadah_m, jarak_pusat_kota_m, jarak_ke_jalan_raya_m,
            skor_kelengkapan_fasilitas, indeks_aksesibilitas_lokasi,
            latitude, longitude, source_url
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        new_id, f"KOS_NEW_{total_now+1}", f"{nama_kost} ({desa})",
        id_lokasi, id_spesifikasi, id_aturan, id_kontrak,
        harga_bulanan, harga_bulanan,
        jarak_kampus, jarak_pasar, jarak_rs, 250, 400, 1500, jarak_jalan,
        skor_fas, indeks_aks, 2.3855, 99.1482, "Input Web Paket A"
    ))
    conn.commit()
    conn.close()
    return {"status": "ok", "new_id_kost": new_id, "message": f"Unit {new_id} ({nama_kost}) berhasil disimpan ke SQLite Star Schema Data Warehouse."}


def get_capabilities(request):
    """Return coarse-grained capabilities without exposing the admin secret."""
    is_admin = bool(ADMIN_API_KEY) and request.headers.get("X-API-Key") == ADMIN_API_KEY
    return {
        "status": "ok",
        "role": "admin" if is_admin else "user",
        "permissions": {
            "read_analytics": True,
            "predict": True,
            "write_warehouse": is_admin,
            "refresh_pipeline": is_admin,
        },
        "admin_configured": bool(ADMIN_API_KEY),
    }


class PaketARequestHandler(SimpleHTTPRequestHandler):
    """HTTP Handler ringan yang melayani Frontend HTML5 dan REST API SQLite + ML."""

    def _send_json(self, data, status=200):
        raw = json.dumps(_json_safe(data), ensure_ascii=False, allow_nan=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        origin = self.headers.get("Origin")
        allowed_origins = {f"http://localhost:{PORT}", f"http://127.0.0.1:{PORT}"}
        if origin in allowed_origins:
            self.send_header("Access-Control-Allow-Origin", origin)
        self.send_header("Vary", "Origin")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _read_json_body(self):
        length_text = self.headers.get("Content-Length", "0")
        try:
            length = int(length_text)
        except ValueError as exc:
            raise RequestValidationError("Content-Length tidak valid.") from exc
        if length < 0 or length > 1024 * 1024:
            raise RequestValidationError("Ukuran request harus kurang dari 1 MB.")
        if length == 0:
            return {}
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RequestValidationError("Body harus berisi JSON UTF-8 yang valid.") from exc
        if not isinstance(payload, dict):
            raise RequestValidationError("Body JSON harus berupa object.")
        return payload

    def _send_api_exception(self, exc):
        if isinstance(exc, RequestValidationError):
            self._send_json({"status": "error", "message": str(exc)}, HTTPStatus.BAD_REQUEST)
        elif isinstance(exc, ModelUnavailableError):
            LOGGER.exception("Model tidak tersedia untuk request %s", self.path)
            self._send_json({"status": "error", "message": str(exc)}, HTTPStatus.SERVICE_UNAVAILABLE)
        else:
            LOGGER.exception("API gagal memproses request %s", self.path)
            self._send_json(
                {"status": "error", "message": "Terjadi kesalahan internal. Periksa log server untuk traceback."},
                HTTPStatus.INTERNAL_SERVER_ERROR
            )

    def do_OPTIONS(self):
        self.send_response(200)
        origin = self.headers.get("Origin")
        allowed_origins = {f"http://localhost:{PORT}", f"http://127.0.0.1:{PORT}"}
        if origin in allowed_origins:
            self.send_header("Access-Control-Allow-Origin", origin)
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Max-Age", "600")
        self.send_header("Vary", "Origin")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/health":
            database_status = "connected"
            model_status = "loaded"
            result = {"status": "ok", "database": database_status, "model": model_status}
            try:
                result["database_records"] = _validate_database()
            except Exception as exc:
                LOGGER.exception("Health check gagal memeriksa SQLite Data Warehouse")
                result["database"] = "error"
                result["database_error"] = str(exc)
            try:
                bundle = load_model_bundle()
                result["model_version"] = bundle["sklearn_version"]
                result["best_algorithm"] = bundle["best_algorithm"]
            except Exception as exc:
                LOGGER.exception("Health check gagal memuat model")
                result["model"] = "error"
                result["model_error"] = str(exc)
            if result["database"] != "connected" or result["model"] != "loaded":
                result["status"] = "degraded"
            self._send_json(result)
            return

        if path == "/api/capabilities":
            self._send_json(get_capabilities(self))
            return

        if path in ("/", "/index.html"):
            if os.path.exists(FRONTEND_HTML_PATH):
                try:
                    with open(FRONTEND_HTML_PATH, "rb") as f:
                        content = f.read()
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Content-Length", str(len(content)))
                    self.end_headers()
                    self.wfile.write(content)
                except OSError as exc:
                    LOGGER.exception("Gagal menyajikan frontend")
                    self._send_json({"status": "error", "message": str(exc)}, HTTPStatus.INTERNAL_SERVER_ERROR)
                return
            self._send_json({"error": "frontend/index.html tidak ditemukan"}, 404)
            return

        if path == "/api/data":
            try:
                self._send_json(get_full_analytics_payload())
            except Exception as exc:
                self._send_api_exception(exc)
            return

        if path == "/api/summary":
            try:
                qs = parse_qs(parsed.query, keep_blank_values=True)
                filters = _read_summary_filters(qs)
                self._send_json(get_price_summary(filters))
            except Exception as exc:
                self._send_api_exception(exc)
            return

        if path == "/api/warehouse":
            qs = parse_qs(parsed.query)
            table_name = qs.get("table", ["fact_sewa_kos"])[0]
            try:
                table_name = ensure_readable_object(table_name)
            except ValueError as exc:
                self._send_json({"status": "error", "message": str(exc)}, HTTPStatus.BAD_REQUEST)
                return
            try:
                with connection() as conn:
                    df_t = pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT 100", conn)
                    total_c = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
                self._send_json({
                    "status": "ok",
                    "table": table_name,
                    "total_rows": int(total_c),
                    "columns": list(df_t.columns),
                    "rows": df_t.to_dict(orient="records")
                })
            except Exception as exc:
                self._send_api_exception(exc)
            return

        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path not in {"/api/predict", "/api/kos", "/api/run-etl"}:
            self._send_json({"status": "error", "message": "Endpoint tidak ditemukan"}, HTTPStatus.NOT_FOUND)
            return
        try:
            body = self._read_json_body()
        except RequestValidationError as exc:
            self._send_api_exception(exc)
            return

        if parsed.path in {"/api/kos", "/api/run-etl"}:
            if not ADMIN_API_KEY:
                self._send_json(
                    {"status": "error", "message": "Operasi admin dinonaktifkan: set TOBAKOST_ADMIN_API_KEY."},
                    HTTPStatus.SERVICE_UNAVAILABLE,
                )
                return
            if self.headers.get("X-API-Key") != ADMIN_API_KEY:
                self._send_json(
                    {"status": "error", "message": "API key admin diperlukan untuk operasi tulis."},
                    HTTPStatus.UNAUTHORIZED,
                )
                return

        if parsed.path == "/api/predict":
            try:
                self._send_json(predict_single_kos(body))
            except Exception as exc:
                self._send_api_exception(exc)
            return

        if parsed.path == "/api/kos":
            try:
                self._send_json(insert_new_kos_to_dw(body))
            except Exception as exc:
                self._send_api_exception(exc)
            return

        if parsed.path == "/api/run-etl":
            try:
                subprocess.run([sys.executable, ETL_SCRIPT_PATH], check=True, cwd=BASE_DIR)
                subprocess.run([sys.executable, TRAIN_SCRIPT_PATH], check=True, cwd=BASE_DIR)
                global MODEL_BUNDLE
                MODEL_BUNDLE = None
                load_model_bundle()
                self._send_json({"status": "ok", "message": "Pipeline ETL & Pelatihan 4 Model Regresi berhasil dijalankan ulang."})
            except Exception as exc:
                self._send_api_exception(exc)
            return


def run_server(port=PORT):
    ensure_database()
    url = f"http://localhost:{port}"
    print("=" * 72)
    print(" TOBAKOST ANALYTICS & ML — ARSITEKTUR PAKET A SIAP!")
    print(f" Database Star Schema : {DB_PATH}")
    print(f" Model Regresi ML     : {MODEL_PKL_PATH}")
    print(f" Frontend HTML5/JS    : {FRONTEND_HTML_PATH}")
    print(f" Buka di Browser      : {url}")
    print("=" * 72)
    try:
        webbrowser.open(url)
    except Exception:
        LOGGER.warning("Browser tidak dapat dibuka otomatis; kunjungi %s", url, exc_info=True)
    server = HTTPServer((HOST, port), PaketARequestHandler)
    try:
        print(f" Health Check         : {url}/api/health")
        print(" Model akan divalidasi saat health check atau saat digunakan.")
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer dihentikan.")
        server.server_close()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    run_server()
