"""Analytics transformations shared by dashboard endpoints."""

import math
import statistics

import numpy as np

from models.features import FEATURE_COLS
from services.database import connection


def get_price_summary():
    """Return warehouse counts and statistics for valid monthly-normalized prices."""
    with connection() as conn:
        rows = conn.execute(
            "SELECT kode_unit_kos, harga_bulanan_norm FROM fact_sewa_kos"
        ).fetchall()

    total_data = len(rows)
    total_kos = len({kode_unit for kode_unit, _ in rows if kode_unit is not None})

    valid_prices = []
    for _, value in rows:
        if not isinstance(value, (int, float)):
            continue
        try:
            price = float(value)
        except OverflowError:
            continue
        if math.isfinite(price) and price > 0:
            valid_prices.append(price)

    statistics_payload = {
        "mean": statistics.mean(valid_prices) if valid_prices else None,
        "median": statistics.median(valid_prices) if valid_prices else None,
        "minimum": min(valid_prices) if valid_prices else None,
        "maximum": max(valid_prices) if valid_prices else None,
    }
    message = None
    if total_data == 0:
        message = "Data kos belum tersedia di warehouse."
    elif not valid_prices:
        message = "Tidak ada harga bulanan valid untuk dihitung."

    return {
        "status": "ok",
        "total_data": total_data,
        "total_kos": total_kos,
        "valid_price_count": len(valid_prices),
        "price_statistics": statistics_payload,
        "message": message,
    }


def enrich_price_analysis(df, models):
    """Add model predictions and pricing diagnostics to an analytics frame."""
    df = df.copy()
    df["pred_rf"] = np.round(
        models["Random Forest Regressor (Tuned)"].predict(df[FEATURE_COLS])
    ).astype(int)
    df["pred_ridge"] = np.round(
        models["Ridge Regression (L2 Tuned)"].predict(df[FEATURE_COLS])
    ).astype(int)
    df["pred_gb"] = np.round(
        models["Gradient Boosting / XGBoost (Tuned)"].predict(df[FEATURE_COLS])
    ).astype(int)
    df["pred_ols"] = np.round(
        models["Linear Regression (Baseline)"].predict(df[FEATURE_COLS])
    ).astype(int)
    df["selisih_rp"] = df["harga_bulanan_norm"] - df["pred_rf"]
    df["selisih_persen"] = ((df["selisih_rp"] / df["pred_rf"]) * 100.0).round(2)
    df["abs_error"] = df["selisih_rp"].abs()
    df["status_kewajaran"] = np.where(
        df["selisih_persen"] < -6.0,
        "Underpriced (Sangat Hemat)",
        np.where(
            df["selisih_persen"] > 6.0,
            "Overpriced (Kemahalan)",
            "Fair Price (Harga Wajar)",
        ),
    )
    return df


def feature_importance(model):
    """Return a stable, display-ready feature importance payload."""
    pairs = sorted(
        zip(FEATURE_COLS, model.feature_importances_),
        key=lambda item: item[1],
        reverse=True,
    )
    return [
        {"feature": name, "importance_pct": round(float(value) * 100.0, 2)}
        for name, value in pairs[:12]
    ]
