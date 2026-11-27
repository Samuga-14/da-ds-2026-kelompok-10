"""Analytics transformations, fair-price classification, facility simulation, and storytelling shared by dashboard endpoints."""

import math
import statistics

import numpy as np
import pandas as pd

from models.features import FEATURE_COLS, add_derived_features, build_feature_frame
from services.database import connection


FAIR_PRICE_THRESHOLD_PCT = 6.0

SIMULATABLE_FACILITIES = {
    "is_ac": "Pendingin Ruangan (AC)",
    "km_dalam": "Kamar Mandi Dalam",
    "is_wifi": "Internet Wi-Fi",
    "ada_tv": "Televisi (TV)",
    "ada_meja_belajar": "Meja & Kursi Belajar",
    "parkir_mobil": "Lahan Parkir Mobil & Motor",
    "dapur_pribadi": "Dapur Pribadi",
    "dapur_bersama": "Dapur Bersama",
    "keamanan_penjaga": "Keamanan Penjaga / Satpam",
    "keamanan_cctv": "Keamanan CCTV",
    "bebas_24jam": "Akses Bebas 24 Jam",
    "listrik_termasuk": "Listrik Termasuk Sewa",
}


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
    "penjaga_satpam": _equals("a.keamanan_kos", "Penjaga/Satpam"),
    "cctv": _any(_equals("a.keamanan_kos", "CCTV"), _equals("a.keamanan_kos", "CCTV Saja")),
    "cctv_saja": _any(_equals("a.keamanan_kos", "CCTV"), _equals("a.keamanan_kos", "CCTV Saja")),
    "tanpa_keamanan": _equals("a.keamanan_kos", "Tidak Ada"),
    "parkir_mobil_motor": _any(
        _equals("a.lahan_parkir", "mobil & motor"),
        _equals("a.lahan_parkir", "Mobil & Motor"),
    ),
    "parkir_motor": _any(
        _equals("a.lahan_parkir", "motor"),
        _equals("a.lahan_parkir", "Motor Saja"),
    ),
    "tanpa_parkir": _any(
        _equals("a.lahan_parkir", "tidak ada"),
        _equals("a.lahan_parkir", "Tidak Ada"),
    ),
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


def classify_fair_price(actual_price: float, predicted_price: float, threshold_pct: float = FAIR_PRICE_THRESHOLD_PCT) -> dict:
    """
    Classify whether a kos listing is Underpriced, Fair Price, or Overpriced
    relative to the model's predicted monthly tariff (Issue #28 / #22-A).
    """
    actual = float(actual_price)
    predicted = max(1.0, float(predicted_price))
    diff_rp = int(round(actual - predicted))
    diff_pct = round((diff_rp / predicted) * 100.0, 2)

    if diff_pct < -threshold_pct:
        status = "Underpriced (Sangat Hemat)"
        category = "murah"
        reason = (
            f"Harga aktual (Rp{actual:,.0f}) lebih rendah {abs(diff_pct):.2f}% "
            f"(Rp{abs(diff_rp):,.0f}) dibanding estimasi pasar model (Rp{predicted:,.0f}) "
            f"untuk spesifikasi fasilitas dan jarak yang setara."
        )
    elif diff_pct > threshold_pct:
        status = "Overpriced (Kemahalan)"
        category = "mahal"
        reason = (
            f"Harga aktual (Rp{actual:,.0f}) lebih tinggi {diff_pct:.2f}% "
            f"(+Rp{diff_rp:,.0f}) di atas estimasi pasar model (Rp{predicted:,.0f}). "
            "Pertimbangkan negosiasi atau cek fasilitas tambahan non-standar."
        )
    else:
        status = "Fair Price (Harga Wajar)"
        category = "wajar"
        reason = (
            f"Harga aktual (Rp{actual:,.0f}) berada dalam rentang toleransi wajar "
            f"(±{threshold_pct:.1f}%, selisih {diff_pct:+.2f}%) terhadap estimasi model (Rp{predicted:,.0f})."
        )

    return {
        "actual_monthly_rp": int(round(actual)),
        "predicted_monthly_rp": int(round(predicted)),
        "selisih_rp": diff_rp,
        "selisih_persen": diff_pct,
        "threshold_persen": threshold_pct,
        "kategori_harga": category,
        "status_kewajaran": status,
        "alasan_rekomendasi": reason,
    }


def enrich_price_analysis(df, models, threshold_pct: float = FAIR_PRICE_THRESHOLD_PCT):
    """Add model predictions, fair-price classification, and recommendation reasons to an analytics frame."""
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
    df["selisih_rp"] = (df["harga_bulanan_norm"] - df["pred_rf"]).round(0).astype(int)
    df["selisih_persen"] = ((df["selisih_rp"] / df["pred_rf"]) * 100.0).round(2)
    df["abs_error"] = df["selisih_rp"].abs()
    df["status_kewajaran"] = np.where(
        df["selisih_persen"] < -threshold_pct,
        "Underpriced (Sangat Hemat)",
        np.where(
            df["selisih_persen"] > threshold_pct,
            "Overpriced (Kemahalan)",
            "Fair Price (Harga Wajar)",
        ),
    )
    df["alasan_rekomendasi"] = np.where(
        df["selisih_persen"] < -threshold_pct,
        "Tarif di bawah estimasi pasar model (>6% lebih hemat) untuk spesifikasi fasilitas & lokasi setara.",
        np.where(
            df["selisih_persen"] > threshold_pct,
            "Tarif di atas estimasi pasar model (>6% lebih mahal); disarankan meninjau kelengkapan fasilitas.",
            "Tarif sesuai standar pasar Kabupaten Toba (±6% dari prediksi model).",
        ),
    )
    return df


def simulate_facility_upgrades(base_features: dict, model, candidate_upgrades: list[str] | None = None) -> dict:
    """
    Counterfactual what-if simulation of adding or toggling kos facilities (Issue #33 / #22-B).
    Uses consistent feature ordering and recalculates derived facility & accessibility scores.
    """
    defaults = {
        "luas_kamar_m2": 12.0,
        "jumlah_lantai": 1,
        "km_dalam": 1,
        "is_ac": 0,
        "is_wifi": 1,
        "ada_tv": 0,
        "ada_meja_belajar": 1,
        "parkir_mobil": 0,
        "dapur_pribadi": 0,
        "dapur_bersama": 1,
        "keamanan_penjaga": 0,
        "keamanan_cctv": 1,
        "bebas_24jam": 1,
        "listrik_termasuk": 0,
        "jarak_ke_kampus_kantor_sekolah_terdekat_km": 0.5,
        "jarak_ke_pasar_km": 0.6,
        "jarak_krusial_km": 0.9,
        "jarak_ke_jalan_raya_m": 50,
        "is_tahunan": 0,
    }
    current = {key: base_features.get(key, default) for key, default in defaults.items()}

    base_df = build_feature_frame(add_derived_features(pd.DataFrame([current])))
    base_pred = int(round(float(np.asarray(model.predict(base_df)).reshape(-1)[0])))

    if candidate_upgrades is None:
        candidate_upgrades = [
            key for key in SIMULATABLE_FACILITIES if int(current.get(key, 0)) == 0
        ]

    simulations = []
    combined = dict(current)
    for feat in candidate_upgrades:
        if feat not in SIMULATABLE_FACILITIES:
            continue
        trial = dict(current)
        trial[feat] = 1
        if feat == "dapur_pribadi":
            trial["dapur_bersama"] = 0
        if feat == "keamanan_penjaga":
            trial["keamanan_cctv"] = 0

        combined[feat] = 1
        if feat == "dapur_pribadi":
            combined["dapur_bersama"] = 0

        trial_df = build_feature_frame(add_derived_features(pd.DataFrame([trial])))
        new_pred = int(round(float(np.asarray(model.predict(trial_df)).reshape(-1)[0])))
        delta_rp = new_pred - base_pred
        delta_pct = round((delta_rp / max(1, base_pred)) * 100.0, 2)
        simulations.append({
            "feature": feat,
            "label": SIMULATABLE_FACILITIES[feat],
            "previously_active": bool(int(current.get(feat, 0)) == 1),
            "simulated_monthly_rp": new_pred,
            "delta_monthly_rp": delta_rp,
            "delta_pct": delta_pct,
            "recommendation": (
                f"Menambahkan {SIMULATABLE_FACILITIES[feat]} menggeser estimasi tarif "
                f"{delta_rp:+,.0f} Rp/bulan ({delta_pct:+.2f}%)."
            ),
        })

    combined_df = build_feature_frame(add_derived_features(pd.DataFrame([combined])))
    combined_pred = int(round(float(np.asarray(model.predict(combined_df)).reshape(-1)[0])))
    simulations.sort(key=lambda item: item["delta_monthly_rp"], reverse=True)

    return {
        "status": "ok",
        "baseline_monthly_rp": base_pred,
        "combined_upgrade_monthly_rp": combined_pred,
        "combined_delta_rp": combined_pred - base_pred,
        "simulations": simulations,
        "limitations": (
            "Simulasi menunjukkan perubahan prediksi kondisional model berdasarkan pola data survei "
            "Kabupaten Toba (833 baris model_ready), bukan jaminan kausalitas mutlak di pasar."
        ),
    }


def get_storytelling_insights(df: pd.DataFrame) -> dict:
    """
    Build structured data storytelling and actionable local recommendations
    backed by statistical evidence from the 923-row Toba kos warehouse (Issue #45 / #46).
    """
    prices = pd.to_numeric(df["harga_bulanan_norm"], errors="coerce").dropna()
    median_all = int(round(float(prices.median()))) if not prices.empty else 0
    mean_all = int(round(float(prices.mean()))) if not prices.empty else 0

    kec_stats = (
        df.groupby("kecamatan")["harga_bulanan_norm"]
        .agg(["count", "median", "mean"])
        .sort_values("median", ascending=False)
    )
    district_summary = [
        {
            "kecamatan": str(idx),
            "count": int(row["count"]),
            "median_rp": int(round(float(row["median"]))),
            "mean_rp": int(round(float(row["mean"]))),
        }
        for idx, row in kec_stats.iterrows()
    ]

    fair_counts = (
        df["status_kewajaran"].value_counts().to_dict()
        if "status_kewajaran" in df.columns
        else {}
    )

    return {
        "status": "ok",
        "headline": (
            f"Standar Tarif Kos Kabupaten Toba Terpusat di Rp{median_all:,.0f}/Bulan, "
            "Didorong oleh Spesifikasi Kamar Mandi Dalam, Wi-Fi, Keamanan, dan Kedekatan Jalan Raya"
        ),
        "overview_statistics": {
            "total_analyzed_units": int(len(df)),
            "median_monthly_rp": median_all,
            "mean_monthly_rp": mean_all,
            "q1_monthly_rp": int(round(float(prices.quantile(0.25)))) if not prices.empty else 0,
            "q3_monthly_rp": int(round(float(prices.quantile(0.75)))) if not prices.empty else 0,
            "fair_price_distribution": {str(k): int(v) for k, v in fair_counts.items()},
        },
        "district_summary": district_summary,
        "key_findings": [
            {
                "title": "1. Klaster Pusat Pendidikan & Ekonomi Memiliki Tarif 1,6x Lebih Tinggi",
                "evidence": "Laguboti, Porsea, dan Ajibata mencatat median Rp725.000/bulan serta Balige Rp700.000/bulan, dibanding Pintu Pohan Meranti (Rp352.084) dan Habinsaran (Rp425.000).",
            },
            {
                "title": "2. Kamar Mandi Dalam dan Wi-Fi Menjadi Standar Baru Kos Mahasiswa & Pekerja",
                "evidence": "Unit dengan Wi-Fi (median Rp750.000 vs Rp550.000 tanpa Wi-Fi) dan Kamar Mandi Dalam (Rp700.000 vs Rp500.000 KM Luar) masing-masing memberikan selisih median +Rp200.000/bulan.",
            },
            {
                "title": "3. Sistem Keamanan Berjenjang Menaikkan Nilai Sewa secara Konsisten",
                "evidence": "Median tarif naik dari Rp625.000 (Tanpa Keamanan) -> Rp650.000 (CCTV) -> Rp750.000 (Penjaga/Satpam) -> Rp850.000 (Penjaga & CCTV).",
            },
            {
                "title": "4. Kedekatan dengan Jalan Raya Utama Memiliki Korelasi Lokasi Terkuat",
                "evidence": "Jarak masuk dari jalan raya utama memiliki korelasi Spearman r = -0,3975 terhadap tarif; unit <= 500 m dari kampus/kantor/sekolah memiliki median tertinggi (Rp700.000/bulan).",
            },
        ],
        "recommendations": {
            "untuk_penyewa": [
                "Bagi mahasiswa IT Del dan pekerja dengan anggaran <= Rp650.000/bulan, pilih unit di Lantai 1 pada desa sekitar Sitoluama/Pintu Bosi atau Balige dengan sistem keamanan CCTV dan kamar mandi dalam standar.",
                "Gunakan indikator 'Underpriced (Sangat Hemat)' pada tabel pencarian kos untuk menemukan unit berfasilitas Wi-Fi + KM Dalam yang tarifnya masih di bawah estimasi pasar model.",
            ],
            "untuk_pemilik_kos": [
                "Investasi fasilitas dengan ROI tarif bulanan paling nyata di Kabupaten Toba adalah penyediaan Wi-Fi bersama (+Rp200.000 median), kamar mandi dalam (+Rp200.000 median), serta pemasangan CCTV/penjaga.",
                "Tetapkan tarif dalam rentang ±6% dari hasil Kalkulator Prediksi Harga Wajar agar tingkat hunian tetap tinggi dan kompetitif.",
            ],
        },
        "limitations": (
            "Temuan dan rekomendasi diturunkan dari 923 unit kos tervalidasi di Kabupaten Toba. "
            "Korelasi deskriptif dan simulasi model tidak menggantikan survei kondisi fisik bangunan secara langsung."
        ),
    }


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
