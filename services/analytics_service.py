"""Analytics transformations shared by dashboard endpoints."""

import math
import statistics

import numpy as np

from models.features import FEATURE_COLS
from services.database import connection


def _contains(column, value):
    return f"INSTR(LOWER(COALESCE({column}, '')), ?) > 0", (value,)


def _equals(column, value):
    return f"{column} = ?", (value,)


def _flag(column):
    return f"COALESCE({column}, 0) = 1", ()


def _any(*conditions):
    sql = " OR ".join(f"({condition[0]})" for condition in conditions)
    params = tuple(value for _, values in conditions for value in values)
    return f"({sql})", params


FACILITY_FILTERS = {
    "dipan": _contains("s.fasilitas_kamar_detail", "dipan"),
    "kasur": _any(_flag("s.ada_kasur"), _contains("s.fasilitas_kamar_detail", "kasur")),
    "lemari": _any(_flag("s.ada_lemari"), _contains("s.fasilitas_kamar_detail", "lemari")),
    "meja_belajar": _any(_flag("s.ada_meja_belajar"), _contains("s.fasilitas_kamar_detail", "meja")),
    "tv": _any(_flag("s.ada_tv"), _contains("s.fasilitas_kamar_detail", "televisi")),
    "cermin": _contains("s.fasilitas_kamar_detail", "cermin"),
    "kulkas_mini": _contains("s.fasilitas_kamar_detail", "kulkas mini"),
    "ventilasi": _contains("s.fasilitas_kamar_detail", "ventilasi"),
    "gorden": _contains("s.fasilitas_kamar_detail", "gorden"),
    "rak_sepatu": _contains("s.fasilitas_kamar_detail", "rak sepatu"),
    "gantungan_baju": _contains("s.fasilitas_kamar_detail", "gantungan baju"),
    "kamar_kosong": _any(
        _contains("s.fasilitas_kamar_detail", "kamar kosong"),
        _contains("s.fasilitas", "kosong"),
    ),
    "ac": _equals("s.ac_non_ac", "ac"),
    "non_ac": _equals("s.ac_non_ac", "non-ac"),
    "km_dalam": _equals("s.tipe_kamar_mandi", "dalam"),
    "km_luar": _equals("s.tipe_kamar_mandi", "luar"),
    "kloset_duduk": _any(
        _flag("s.kloset_duduk"),
        _contains("s.kelengkapan_kamar_mandi", "duduk"),
    ),
    "kloset_jongkok": _contains("s.kelengkapan_kamar_mandi", "jongkok"),
    "shower": _any(
        _flag("s.ada_shower"),
        _contains("s.kelengkapan_kamar_mandi", "shower"),
    ),
    "water_heater": _any(
        _flag("s.ada_water_heater"),
        _contains("s.kelengkapan_kamar_mandi", "water heater"),
    ),
    "bak_mandi": _contains("s.kelengkapan_kamar_mandi", "bak mandi"),
    "air_pdam": _equals("a.sumber_air_utama", "Air PDAM"),
    "air_sumur_bor": _equals("a.sumber_air_utama", "Air Sumur Bor"),
    "air_sumur_gali": _equals("a.sumber_air_utama", "Air Sumur Gali"),
    "air_gunung": _equals("a.sumber_air_utama", "Air Gunung"),
    "wifi": _equals("a.wifi_non_wifi", "wifi"),
    "non_wifi": _equals("a.wifi_non_wifi", "non-wifi"),
    "dapur_pribadi": _any(
        _equals("a.dapur", "pribadi"),
        _contains("a.fasilitas_dapur_kulkas", "pribadi"),
    ),
    "dapur_bersama_kulkas": _contains("a.fasilitas_dapur_kulkas", "dapur bersama dengan kulkas"),
    "dapur_bersama_tanpa_kulkas": _contains("a.fasilitas_dapur_kulkas", "dapur bersama tanpa kulkas"),
    "kulkas_bersama": _contains("a.fasilitas_dapur_kulkas", "hanya kulkas bersama"),
    "tanpa_dapur": _any(
        _equals("a.dapur", "tidak ada"),
        _contains("a.fasilitas_dapur_kulkas", "tidak ada"),
    ),
    "laundry_kos": _contains("a.fasilitas_cuci_jemur", "laundry"),
    "mesin_cuci_jemur": _contains("a.fasilitas_cuci_jemur", "mesin cuci bersama dan area jemuran"),
    "mesin_cuci_saja": _contains("a.fasilitas_cuci_jemur", "hanya mesin cuci bersama"),
    "jemuran_saja": _contains("a.fasilitas_cuci_jemur", "hanya area penjemuran"),
    "tanpa_cuci_jemur": _contains("a.fasilitas_cuci_jemur", "tidak ada"),
    "penjaga_cctv": _equals("a.keamanan_kos", "Penjaga & CCTV"),
    "cctv_saja": _equals("a.keamanan_kos", "CCTV Saja"),
    "tanpa_keamanan": _equals("a.keamanan_kos", "Tidak Ada"),
    "parkir_mobil_motor": _equals("a.lahan_parkir", "mobil & motor"),
    "parkir_motor": _equals("a.lahan_parkir", "motor"),
    "tanpa_parkir": _equals("a.lahan_parkir", "tidak ada"),
    "bebas_24jam": _equals("a.aturan_jam_malam_masuk", "Bebas 24 Jam"),
    "jam_malam": _equals("a.aturan_jam_malam_masuk", "Ada Batas Jam Malam"),
    "listrik_termasuk": _equals("a.skema_biaya_listrik", "termasuk sewa"),
    "listrik_token": _equals("a.skema_biaya_listrik", "token sendiri"),
}


def get_price_summary(filters=None):
    """Return filtered warehouse counts and statistics for valid monthly-normalized prices."""
    if filters is None:
        filters = {}
    if not isinstance(filters, dict):
        raise TypeError("filters harus berupa dictionary.")

    def selected_value(name):
        value = filters.get(name)
        if value is None:
            return None
        value = str(value).strip()
        if not value or value.upper() == "ALL":
            return None
        return value

    query = """
        SELECT f.kode_unit_kos, f.harga_bulanan_norm
        FROM fact_sewa_kos AS f
        JOIN dim_lokasi AS l ON f.id_lokasi = l.id_lokasi
        JOIN dim_spesifikasi_kamar AS s ON f.id_spesifikasi = s.id_spesifikasi
        JOIN dim_fasilitas_aturan AS a ON f.id_aturan = a.id_aturan
        JOIN dim_kontrak_sewa AS k ON f.id_kontrak = k.id_kontrak
        WHERE 1 = 1
    """
    params = []

    kecamatan = selected_value("kecamatan")
    if kecamatan is not None:
        query += " AND l.kecamatan = ?"
        params.append(kecamatan)

    kategori_penghuni = selected_value("kategori_penghuni")
    if kategori_penghuni is not None:
        query += " AND LOWER(a.kategori_penghuni) = LOWER(?)"
        params.append(kategori_penghuni)

    sewa_tahunan_bulanan = selected_value("sewa_tahunan_bulanan")
    if sewa_tahunan_bulanan is not None:
        query += " AND LOWER(k.sewa_tahunan_bulanan) = LOWER(?)"
        params.append(sewa_tahunan_bulanan)

    tahun_mulai_sewa = selected_value("tahun_mulai_sewa")
    if tahun_mulai_sewa is not None:
        query += " AND k.tahun_mulai_sewa = ?"
        params.append(tahun_mulai_sewa)

    harga_min = selected_value("harga_min")
    if harga_min is not None:
        query += " AND f.harga_bulanan_norm >= ?"
        params.append(float(harga_min))

    harga_max = selected_value("harga_max")
    if harga_max is not None:
        query += " AND f.harga_bulanan_norm <= ?"
        params.append(float(harga_max))

    fasilitas = selected_value("fasilitas")
    if fasilitas is not None:
        if fasilitas not in FACILITY_FILTERS:
            raise ValueError(f"Fasilitas tidak dikenal: {fasilitas}.")
        condition, values = FACILITY_FILTERS[fasilitas]
        query += f" AND {condition}"
        params.extend(values)

    with connection() as conn:
        rows = conn.execute(query, params).fetchall()

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
    active_filters = any(
        selected_value(name) is not None
        for name in (
            "kecamatan",
            "kategori_penghuni",
            "sewa_tahunan_bulanan",
            "tahun_mulai_sewa",
            "harga_min",
            "harga_max",
            "fasilitas",
        )
    )
    if total_data == 0 and active_filters:
        message = "Tidak ada data yang cocok dengan filter."
    elif total_data == 0:
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
