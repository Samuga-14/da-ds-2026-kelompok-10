"""
Normalize and strictly clean the Toba kos survey dataset (`data/raw/Survey_Kos_Fix.csv`, 569 rows)
without modifying the raw CSV file.

Key preprocessing & logical cleaning steps:
1. Entity & Kos Name Standardization (`nama_kost`):
   - Strips leading/trailing and duplicate internal spaces (`'Kos  birong'` -> `'Kos Birong'`).
   - Standardizes capitalization (preserving acronyms like `LH`, `GKPI`, `HKBP`, `SAS`, `IT`).
   - Maps missing/placeholder names (`'-'`, `'Tidak ada'`, `'Tidak ada nama'`) to `'Kos Tanpa Nama'`.
   - Flags non-kos records (`'Bukan kos tapi rumah keluarga'`).
2. Room Area (`luas_kamar_m2`):
   - Evaluates multiplication dimensions (`'4x4'` -> `16.0`, `'3,5x5'` -> `17.5`, `'4*3'` -> `12.0`).
   - Converts single-dimension side length entries (`'2'`, `'2m²'`, `'3'`, `'3 m2'`, `'3 meter'`, `'3.5'`, `'4'`, `'4 m'`)
     where respondents typed 1 side length in meters into logical square area (`s * s`: `4.0`, `9.0`, `12.25`, `16.0` m²).
   - Corrects obvious extra-zero typos (`2000` -> `200`).
   - Flags whole-building / house area outliers (`luas_kamar_m2 > 36` m² or `< 4` m²) as invalid room sizes.
3. Distances (all in meters `_m`, plus categorical `klasifikasi_jarak_*`):
   - Extracts destination category (`Kampus IT Del`, `Kampus`, `Kantor`, `Sekolah`).
   - Converts `km` inputs to meters (`'1,5 km'` -> `1500`) and single-digit `1`–`5` km shorthands (`1000`–`5000` m).
   - Fixes typo `300010` -> `3000` m.
   - Logical zero-distance rule: for external facilities (`jarak_laundry_m`, `jarak_pasar_minimarket_m`,
     `jarak_fasilitas_kesehatan_m`, `jarak_tempat_ibadah_m`, `jarak_pusat_kota_m`), `0` m is treated as a missing
     placeholder (`NaN`) and imputed with the same-kecamatan median (whereas `0` m for `jarak_jalan_raya_m` is valid).
4. Room Floor (`jumlah_lantai` & `kategori_lantai`):
   - Maps `'bawah tanah'` -> `1`, caps floors `> 5` (e.g. `9`) to numeric `4` with label `'4 - 5'`.
5. Rent Price (`harga_sewa` & `harga_bulanan_norm`):
   - Strips thousand separators (`750.000` -> `750000`), scales shorthand entries (`7` Per Tahun -> `7000000`,
     `250`/`500`/`700`/`900` -> `250000`–`900000`, `10000`/`60000`/`70000` -> `100000`–`700000`).
   - Normalizes annual rent to monthly equivalent (`/ 12`).
   - Enforces strict logical monthly kos rent bounds (`Rp150.000 <= harga_bulanan_norm <= Rp5.000.000`).
6. Extra Cost (`ada_biaya_tambahan` & `biaya_tambahan_rp`):
   - Parses `rb`/`ribu` suffixes (`100rb` -> `100000`) and shorthand thousands (`40` -> `40000`).
   - Enforces `biaya_tambahan_rp = 0` when `ada_biaya_tambahan == 'Tidak'` (fixing contradictory entries like `8150000`).
   - Reconciles `ada_biaya_tambahan = 'Tidak'` when respondent answered `'Ada'` but left nominal empty/`0`.
7. Logical Facility & Categorical Standardization:
   - Bedroom facilities: strips contradictory `'Kamar Kosong (...)'` label when actual furniture (`Kasur`, `Lemari`,
     `Meja`, `Dipan`) is present; adds `is_kamar_kosong` flag.
   - Bathroom facilities: resolves contradictory dual selection `'Toilet duduk, Toilet Jongkok'` based on `km_dalam`.
   - `keamanan_kos`: merges `'CCTV Saja'` and `'CCTV'` into `'CCTV'`.
   - `tipe_kamar_mandi`: standardizes to `'dalam'` / `'luar'`.
   - `lahan_parkir`: standardizes to `'Mobil & Motor'`, `'Motor Saja'`, `'Tidak Ada'`.
   - `aturan_jam_malam`: standardizes to `'Bebas 24 Jam'` / `'Ada Batas Jam Malam'`.
   - `status_penyewa`: merges `'Siswa'`, `'siswa sma'`, `'Pelajar SMA'`, `'Siswa/Pelajar'` -> `'Pelajar'`.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_RAW_PATH = BASE_DIR / "data" / "raw" / "Survey_Kos_Fix.csv"
FALLBACK_RAW_PATH = BASE_DIR / "data" / "raw" / "Survey_Kos.csv"
RAW_PATH = DEFAULT_RAW_PATH if DEFAULT_RAW_PATH.exists() else FALLBACK_RAW_PATH
STAGING_DIR = BASE_DIR / "data" / "staging"
REPORT_DIR = BASE_DIR / "data" / "quality"
STAGING_PATH = STAGING_DIR / "survey_clean_v1.csv"
REPORT_PATH = REPORT_DIR / "survey_quality_v1.json"


def find_column(df: pd.DataFrame, *phrases: str, required: bool = True) -> str | None:
    for column in df.columns:
        normalized = " ".join(str(column).lower().split())
        if all(phrase.lower() in normalized for phrase in phrases):
            return column
    if required:
        raise KeyError(f"Kolom tidak ditemukan: {phrases}")
    return None


def text_value(value) -> str:
    if pd.isna(value):
        return ""
    return " ".join(str(value).strip().split())


def normalize_kos_name(value) -> str:
    """Clean kos name: collapse whitespace, handle placeholders, and standardize title casing."""
    raw = text_value(value)
    if not raw or raw.lower() in ("-", "tidak ada", "tidak ada nama", "kosong", "tanpa nama"):
        return "Kos Tanpa Nama"
    titled = raw.title()
    # Preserve common acronyms and Roman numerals
    for acronym in ("LH", "GKPI", "HKBP", "SAS", "IT", "II", "III", "IV"):
        titled = re.sub(rf"\b{acronym.title()}\b", acronym, titled)
    return titled


def numeric_value(value) -> float:
    """Parse common Indonesian survey numeric formats (e.g. '40.000', '550000', '1,5')."""
    if pd.isna(value):
        return np.nan
    text = str(value).strip().replace(" ", "")
    if not text:
        return np.nan
    match = re.search(r"-?\d+(?:[.,]\d+)*", text)
    if not match:
        return np.nan

    number = match.group(0)
    if "," in number and "." in number:
        number = number.replace(".", "").replace(",", ".")
    elif "," in number:
        if re.search(r",\d{3}$", number):
            number = number.replace(",", "")
        else:
            number = number.replace(".", "").replace(",", ".")
    elif re.search(r"\.\d{3}(?:\.\d{3})*$", number):
        number = number.replace(".", "")
    return float(number)


def parse_room_area(value) -> float:
    """
    Parse room area in m2:
    - Evaluates multiplication expressions ('4x3', '3,5x5', '4*3') -> 12.0, 17.5, 12.0.
    - Converts 1D side-length shorthand (1.5 <= val <= 4.0, e.g. '3', '3 m2', '3 meter', '4 m')
      into logical square room area (val * val -> 9.0, 16.0 m2).
    - Fixes obvious extra-zero typo ('2000' -> 200.0).
    """
    if pd.isna(value):
        return np.nan
    text = str(value).strip().lower()
    if not text:
        return np.nan

    mult_match = re.search(
        r"(\d+(?:[.,]\d+)?)\s*(?:m2|m²|meter|m)?\s*[x×*]\s*(\d+(?:[.,]\d+)?)",
        text,
    )
    if mult_match:
        a = float(mult_match.group(1).replace(",", "."))
        b = float(mult_match.group(2).replace(",", "."))
        area = round(a * b, 2)
    else:
        area = numeric_value(text)
        if not pd.isna(area) and 1.5 <= area <= 4.0:
            # Respondent entered 1 side length in meters (e.g. '3', '3 meter', '4 m') instead of m2 area
            area = round(area * area, 2)

    if pd.isna(area):
        return np.nan

    # Fix obvious extra-zero typo (e.g., 2000 m2 -> 200 m2)
    if area >= 1000:
        area = round(area / 10.0, 2)
    return float(area)


def parse_campus_distance(value) -> tuple[str, float]:
    """Extract destination category and distance in meters from question 6."""
    if pd.isna(value):
        return "Tidak Disebutkan", np.nan
    raw = text_value(value)
    if not raw:
        return "Tidak Disebutkan", np.nan
    lower = raw.lower()

    if "del" in lower:
        destination = "Kampus IT Del"
    elif "kampus" in lower or "universitas" in lower:
        destination = "Kampus"
    elif "sekolah" in lower or "sma" in lower or "smp" in lower:
        destination = "Sekolah"
    elif "kantor" in lower or "kerja" in lower:
        destination = "Kantor"
    else:
        destination = "Tidak Disebutkan"

    is_km = bool(re.search(r"\b(?:km|kilometer)\b", lower))
    val = numeric_value(lower)
    if pd.isna(val) or val <= 0:
        return destination, np.nan

    if is_km:
        meters = val * 1000.0
    elif 0 < val < 10:
        # Shorthand e.g. 'Kampus 3', 'kampus 5' -> 3000m, 5000m
        meters = val * 1000.0
    else:
        meters = val
    return destination, round(float(meters), 0)


def parse_distance_meters(value, allow_zero: bool = False) -> float:
    """
    Normalize facility distance in meters:
    - Converts km inputs and single-digit 1-4 km shorthands to meters.
    - Fixes typo 300010 -> 3000 m.
    - If allow_zero is False (for external public facilities like laundry/market),
      treats 0 m as missing (NaN) so it can be imputed with kecamatan median.
    """
    if pd.isna(value):
        return np.nan
    raw = text_value(value).lower()
    if not raw:
        return np.nan
    is_km = bool(re.search(r"\b(?:km|kilometer)\b", raw))
    val = numeric_value(raw)
    if pd.isna(val) or val < 0:
        return np.nan
    if val == 0:
        return 0.0 if allow_zero else np.nan
    if is_km:
        meters = val * 1000.0
    elif val == 300010:
        meters = 3000.0
    elif 0 < val <= 4:
        meters = val * 1000.0
    else:
        meters = val
    return round(float(meters), 0)


def classify_distance_meters(meters: float) -> str:
    """Classify distance in meters into interpretable accessibility tiers."""
    if pd.isna(meters):
        return "Tidak Diketahui"
    if meters <= 500:
        return "Sangat Dekat (<= 500 m)"
    if meters <= 1000:
        return "Dekat (501 - 1000 m)"
    if meters <= 3000:
        return "Sedang (1001 - 3000 m)"
    return "Jauh (> 3000 m)"


def parse_floor(value) -> tuple[float, str]:
    """Normalize floor: 'bawah tanah' -> 1, > 5 -> numeric 4 with category '4 - 5'."""
    if pd.isna(value):
        return np.nan, "Tidak Diketahui"
    raw = text_value(value).lower()
    if not raw:
        return np.nan, "Tidak Diketahui"
    if "bawah tanah" in raw or "basement" in raw or "dasar" in raw:
        return 1.0, "1"
    val = numeric_value(raw)
    if pd.isna(val) or val < 1:
        return 1.0, "1"
    if val > 5:
        return 4.0, "4 - 5"
    if val >= 4:
        return float(int(round(val))), "4 - 5"
    return float(int(round(val))), str(int(round(val)))


def parse_rent_price(value, is_annual: int) -> float:
    """Normalize rent price to full Rupiah integer (e.g. 7 -> 700000/7000000, 100.000 -> 100000)."""
    val = numeric_value(value)
    if pd.isna(val) or val <= 0:
        return np.nan

    # Handle shorthand values where respondents omitted thousand/million zeros
    if val < 100:
        # Single/double digit like '7' -> Rp700.000 (or Rp7.000.000 if annual)
        val = val * (1_000_000.0 if is_annual == 1 else 100_000.0)
    elif val < 2_000:
        # 3-digit shorthand like 250, 500, 700, 900 -> Rp250.000 - Rp900.000
        val = val * 1_000.0
    elif val < 100_000:
        # 4-5 digit missing one zero like 10000 -> 100000, 60000 -> 600000, 70000 -> 700000
        val = val * 10.0

    return round(float(val), 0)


def parse_extra_cost(value, has_extra_text: str) -> float:
    """Normalize extra cost in Rupiah, handling '100rb', '40' -> 40000, and enforcing 0 if has_extra == 'Tidak'."""
    if str(has_extra_text).strip().lower() in ("tidak", "tidak ada", ""):
        return 0.0
    if pd.isna(value):
        return 0.0
    raw = text_value(value).lower()
    if not raw or any(phrase in raw for phrase in ("tidak", "tak", "kosong", "-")):
        return 0.0
    is_ribu = bool(re.search(r"\b(?:rb|ribu|k)\b|\d+(?:rb|ribu|k)\b", raw))
    val = numeric_value(raw)
    if pd.isna(val) or val <= 0:
        return 0.0
    if is_ribu or val < 1000:
        val = val * 1000.0
    return round(float(val), 0)


def clean_bedroom_facilities(raw_text: str) -> str:
    """
    Logical cleaning of bedroom facilities:
    If actual furniture/facilities exist alongside 'Kamar Kosong (...)', strip the contradictory
    'Kamar Kosong' option so the text and binary flags are 100% consistent.
    """
    text = text_value(raw_text)
    if not text:
        return "Kamar Kosong"
    if "kamar kosong" in text.lower():
        cleaned = re.sub(
            r",?\s*Kamar Kosong\s*(?:\([^)]*\))?\s*,?",
            ", ",
            text,
            flags=re.IGNORECASE,
        )
        cleaned = ", ".join(part.strip() for part in cleaned.split(",") if part.strip())
        return cleaned if cleaned else "Kamar Kosong"
    return text


def normalize_desa(value: str) -> str:
    text = text_value(value)
    if not text:
        return "Tidak Disebutkan"
    cleaned = re.sub(r"^(?:desa|kelurahan)\s+", "", text, flags=re.IGNORECASE).strip()
    lower = cleaned.lower()
    mapping = {
        "pintubosi": "Pintu Bosi",
        "pintu bosi": "Pintu Bosi",
        "pardede onan": "Pardede Onan",
        "soposurung": "Soposurung",
        "belakang gereja soposurung": "Soposurung",
        "simpang hkbp sopo surung": "Soposurung",
        "simpang hkbp soposurung": "Soposurung",
        "sitoluama": "Sitoluama",
        "sitolu ama,jln arjuna": "Sitoluama",
        "balige 1": "Balige I",
        "balige i": "Balige I",
        "balige 2": "Balige II",
        "balige ii": "Balige II",
        "balige iii": "Balige III",
        "gang demak, balige iii": "Balige III",
        "silalahi pagarbatu": "Silalahi Pagar Batu",
        "silalahi pagar batu": "Silalahi Pagar Batu",
        "pagarbatu": "Silalahi Pagar Batu",
        "napitupulu bagasan": "Napitupulu Bagasan",
        "napitupulu": "Napitupulu Bagasan",
        "sangkar nihuta 1 balige": "Sangkar Nihuta",
        "sangkar nihuta, kec. balige": "Sangkar Nihuta",
        "sangkar nihuta": "Sangkar Nihuta",
        "lumban dolok hauma bange": "Lumban Dolok Haume Bange",
        "lumban dolok haume bange, kec. balige, kabupaten toba, sumatera utara": "Lumban Dolok Haume Bange",
        "lumban dolok haume bange": "Lumban Dolok Haume Bange",
        "sibolahotang sas": "Sibolahotang SAS",
        "sibolo hotanghas": "Sibolahotang SAS",
        "parparean": "Parparean",
    }
    if lower in mapping:
        return mapping[lower]
    if "narumonda v" in lower:
        return "Narumonda V"
    if "bahas huta" in lower:
        return "Bahas Huta"
    titled = cleaned.title()
    titled = re.sub(r"\b(Ii|Iii|Iv|Vi)\b", lambda m: m.group(1).upper(), titled)
    titled = re.sub(r"\bSas\b", "SAS", titled)
    return titled


def normalize_security(value: str) -> str:
    """Standardize security values, merging 'CCTV Saja' and 'CCTV' into 'CCTV'."""
    text = text_value(value)
    lower = text.lower()
    if "penjaga" in lower and "cctv" in lower:
        return "Penjaga & CCTV"
    if "penjaga" in lower or "satpam" in lower:
        return "Penjaga/Satpam"
    if "cctv" in lower:
        return "CCTV"
    return "Tidak Ada"


def normalize_parking(value: str) -> str:
    text = text_value(value).lower()
    if "mobil" in text:
        return "Mobil & Motor"
    if "motor" in text:
        return "Motor Saja"
    return "Tidak Ada"


def normalize_night_rule(value: str) -> str:
    text = text_value(value).lower()
    if "bebas" in text:
        return "Bebas 24 Jam"
    return "Ada Batas Jam Malam"


def normalize_bathroom_type(value: str) -> str:
    text = text_value(value).lower()
    if "dalam" in text:
        return "dalam"
    return "luar"


def normalize_survey(raw_path: Path = RAW_PATH):
    df = pd.read_csv(raw_path)
    raw_count = len(df)

    # Measure raw quality metrics before preprocessing
    raw_missing_cells = int(df.isna().sum().sum())
    raw_exact_duplicates = int(df.duplicated(keep=False).sum())

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
    has_extra_cost = find_column(df, "biaya tambahan", "di luar")
    if has_extra_cost is None:
        has_extra_cost = find_column(df, "biaya tambahan")
    extra_cost = find_column(df, "total biaya tambahan")
    timestamp_col = find_column(df, "timestamp", required=False)

    canonical = pd.DataFrame()
    if timestamp_col:
        canonical["timestamp_survei"] = df[timestamp_col].map(text_value)

    raw_names = df[name].map(text_value)
    canonical["nama_kost"] = raw_names.map(normalize_kos_name)
    is_non_kos = raw_names.str.contains("bukan kos", case=False, na=False)

    canonical["kecamatan"] = df[kecamatan].map(text_value).str.strip().str.title()
    canonical["desa_kelurahan"] = df[desa].map(normalize_desa)
    canonical["kategori_penghuni"] = df[category].map(text_value).str.strip().str.title()

    canonical["status_penyewa"] = (
        df[occupant_status]
        .map(text_value)
        .str.lower()
        .replace(
            {
                "siswa": "pelajar",
                "siswa sma": "pelajar",
                "pelajar sma": "pelajar",
                "siswa/pelajar": "pelajar",
                "pelajar": "pelajar",
                "": "tidak disebutkan",
            }
        )
        .str.title()
    )

    # Campus/School/Office distance and destination
    parsed_campus = df[campus_distance].map(parse_campus_distance)
    canonical["tujuan_utama"] = [item[0] for item in parsed_campus]
    canonical["jarak_kampus_sekolah_tempatkerja_m"] = [item[1] for item in parsed_campus]

    distance_sources = {
        "jarak_pasar_minimarket_m": (market_distance, False),
        "jarak_fasilitas_kesehatan_m": (health_distance, False),
        "jarak_tempat_ibadah_m": (worship_distance, False),
        "jarak_laundry_m": (laundry_distance, False),
        "jarak_pusat_kota_m": (center_distance, False),
        "jarak_jalan_raya_m": (road_distance, True),
    }
    imputed_zero_distances = 0
    for output_col, (source_col, allow_zero) in distance_sources.items():
        if not allow_zero:
            imputed_zero_distances += int(
                df[source_col].map(text_value).isin(["0", "0.0"]).sum()
            )
        canonical[output_col] = [
            parse_distance_meters(v, allow_zero=allow_zero) for v in df[source_col]
        ]

    # Impute missing/0 external distances with same-kecamatan median (fallback global median)
    distance_cols_m = [
        "jarak_kampus_sekolah_tempatkerja_m",
        "jarak_pasar_minimarket_m",
        "jarak_fasilitas_kesehatan_m",
        "jarak_tempat_ibadah_m",
        "jarak_laundry_m",
        "jarak_pusat_kota_m",
        "jarak_jalan_raya_m",
    ]
    for col_m in distance_cols_m:
        global_med = canonical[col_m].median()
        canonical[col_m] = (
            canonical.groupby("kecamatan")[col_m]
            .transform(lambda s: s.fillna(s.median()))
            .fillna(global_med)
            .round(0)
        )

    for col_m in distance_cols_m:
        class_col = re.sub(r"_m$", "", col_m).replace("jarak_", "klasifikasi_jarak_")
        canonical[class_col] = canonical[col_m].map(classify_distance_meters)

    # Room floor and room area
    parsed_floors = df[room_floor].map(parse_floor)
    canonical["jumlah_lantai"] = [item[0] for item in parsed_floors]
    canonical["kategori_lantai"] = [item[1] for item in parsed_floors]
    canonical["luas_kamar_m2"] = df[room_area].map(parse_room_area)

    # Bathroom type and facilities (with logical resolution of dual kloset duduk + jongkok)
    canonical["tipe_kamar_mandi"] = df[bathroom_type].map(normalize_bathroom_type)
    canonical["km_dalam"] = canonical["tipe_kamar_mandi"].eq("dalam").astype(int)
    canonical["kelengkapan_kamar_mandi"] = df[bathroom_facilities].map(text_value)

    raw_duduk = canonical["kelengkapan_kamar_mandi"].str.contains("duduk", case=False, na=False)
    raw_jongkok = canonical["kelengkapan_kamar_mandi"].str.contains("jongkok", case=False, na=False)
    both_kloset = raw_duduk & raw_jongkok
    resolved_dual_kloset_count = int(both_kloset.sum())

    # If respondent checked both duduk & jongkok: assign kloset_duduk for km_dalam, kloset_jongkok for km_luar
    canonical["kloset_duduk"] = np.where(
        both_kloset, canonical["km_dalam"].eq(1), raw_duduk
    ).astype(int)
    canonical["kloset_jongkok"] = np.where(
        both_kloset, canonical["km_dalam"].eq(0), raw_jongkok
    ).astype(int)
    canonical["ada_shower"] = (
        canonical["kelengkapan_kamar_mandi"].str.contains("shower", case=False, na=False).astype(int)
    )
    canonical["ada_water_heater"] = (
        canonical["kelengkapan_kamar_mandi"].str.contains("water heater", case=False, na=False).astype(int)
    )
    canonical["ada_bak_mandi"] = (
        canonical["kelengkapan_kamar_mandi"].str.contains("bak mandi", case=False, na=False).astype(int)
    )
    canonical["ada_gayung"] = (
        canonical["kelengkapan_kamar_mandi"].str.contains("gayung", case=False, na=False).astype(int)
    )

    # Bedroom facilities (with logical resolution of contradictory 'Kamar Kosong')
    raw_facilities = df[bedroom_facilities].map(text_value)
    facilities = raw_facilities.map(clean_bedroom_facilities)
    contradictory_kamar_kosong_count = int(
        (
            raw_facilities.str.contains("kamar kosong", case=False, na=False)
            & ~facilities.str.lower().eq("kamar kosong")
        ).sum()
    )
    canonical["fasilitas_kamar_detail"] = facilities
    for name_output, phrase in {
        "ada_dipan": "dipan",
        "ada_kasur": "kasur",
        "ada_lemari": "lemari",
        "ada_meja_belajar": "meja",
        "ada_tv": "televisi",
        "ada_cermin": "cermin",
        "ada_kulkas_pribadi": "kulkas",
        "ada_ventilasi": "ventilasi",
        "ada_gorden": "gorden",
        "ada_rak_sepatu": "rak sepatu",
        "ada_gantungan_baju": "gantungan baju",
    }.items():
        canonical[name_output] = facilities.str.contains(phrase, case=False, na=False).astype(int)

    canonical["ac"] = df[ac].map(text_value).str.lower().eq("ada").astype(int)
    canonical["skema_listrik"] = df[electricity].map(text_value)
    canonical["listrik_termasuk"] = (
        canonical["skema_listrik"].str.contains("termasuk", case=False, na=False).astype(int)
    )
    canonical["periode_sewa"] = df[period].map(text_value).str.strip().str.lower()
    canonical["sewa_tahunan"] = canonical["periode_sewa"].eq("per tahun").astype(int)

    # Standardized integer Rupiah rent price (e.g. 7 -> 700000/7000000, 100.000 -> 100000)
    canonical["harga_sewa"] = [
        parse_rent_price(val, annual)
        for val, annual in zip(df[rent], canonical["sewa_tahunan"])
    ]
    canonical["harga_bulanan_norm"] = np.where(
        canonical["sewa_tahunan"].eq(1),
        canonical["harga_sewa"] / 12.0,
        canonical["harga_sewa"],
    ).round(0)

    # Security, parking, rules, utilities
    canonical["keamanan_kos"] = df[security].map(normalize_security)
    canonical["lahan_parkir"] = df[parking].map(normalize_parking)
    canonical["aturan_jam_malam"] = df[night_rule].map(normalize_night_rule)
    canonical["kapasitas_kamar"] = df[capacity].map(text_value)
    canonical["wifi"] = df[wifi].map(text_value).str.strip().str.lower()
    canonical["is_wifi"] = canonical["wifi"].eq("ada").astype(int)
    canonical["sumber_air"] = df[water].map(text_value)
    canonical["fasilitas_dapur"] = df[kitchen].map(text_value)
    canonical["fasilitas_cuci_jemur"] = (
        df[laundry]
        .map(text_value)
        .replace("", "Hanya area penjemuran tanpa mesin cuci")
    )
    canonical["area_tempat_makan"] = df[eating_area].map(text_value)

    canonical["status_harga"] = df[validity].map(text_value)
    canonical["harga_masih_berlaku"] = (
        canonical["status_harga"].str.startswith("Ya", na=False).astype(int)
    )
    canonical["kos_aktif"] = (
        ~canonical["status_harga"].str.contains("tidak beroperasi", case=False, na=False)
    ).astype(int)

    canonical["biaya_sewa_sudah_mencakup"] = (
        df[included_cost].map(text_value).replace("", "Tidak Disebutkan")
    )
    raw_has_extra = df[has_extra_cost].map(text_value).replace("", "Tidak").str.title()
    parsed_extra_rp = [
        parse_extra_cost(val, flag)
        for val, flag in zip(df[extra_cost], raw_has_extra)
    ]
    canonical["biaya_tambahan_rp"] = parsed_extra_rp
    # Logical consistency: if nominal extra cost is 0, ada_biaya_tambahan must be 'Tidak'
    canonical["ada_biaya_tambahan"] = np.where(
        canonical["biaya_tambahan_rp"] > 0, "Ada", "Tidak"
    )

    # Duplicate and quality flags
    canonical["exact_duplicate"] = df.duplicated(keep=False).astype(int)
    duplicate_key = [
        "nama_kost",
        "kecamatan",
        "desa_kelurahan",
        "jumlah_lantai",
        "luas_kamar_m2",
        "periode_sewa",
        "harga_sewa",
    ]
    canonical["duplicate_logis"] = canonical.duplicated(subset=duplicate_key, keep=False).astype(int)

    # Strict logical domain bounds for a single kos room
    valid_price = canonical["harga_bulanan_norm"].between(150_000, 5_000_000)
    valid_area = canonical["luas_kamar_m2"].between(4.0, 36.0)
    valid_numeric = valid_price & valid_area & (~is_non_kos)

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
        if is_non_kos.loc[index]:
            reasons.append("bukan entitas kos (rumah keluarga)")
        if not valid_price.loc[index]:
            reasons.append("harga bulanan tidak logis (< Rp150rb atau > Rp5jt)")
        if not valid_area.loc[index]:
            reasons.append("luas kamar tidak logis (< 4 m2 atau > 36 m2)")
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

    missing_after = {
        column: int(count)
        for column, count in canonical.isna().sum().sort_values(ascending=False).items()
        if count
    }
    report = {
        "raw_path": str(raw_path),
        "raw_rows": raw_count,
        "raw_columns": len(df.columns),
        "staging_path": str(STAGING_PATH),
        "staging_rows": len(canonical),
        "staging_columns": len(canonical.columns),
        "exact_duplicates": int(canonical["exact_duplicate"].sum()),
        "logical_duplicate_rows": int(canonical["duplicate_logis"].sum()),
        "accepted_for_analysis": int(canonical["accepted_for_analysis"].sum()),
        "model_ready": int(canonical["model_ready"].sum()),
        "price_anomaly_iqr": int(canonical["price_anomaly_iqr"].sum()),
        "price_iqr_bounds": {"lower": round(float(lower), 2), "upper": round(float(upper), 2)},
        "logical_cleaning_actions": {
            "imputed_zero_external_distances": imputed_zero_distances,
            "resolved_contradictory_kamar_kosong": contradictory_kamar_kosong_count,
            "resolved_dual_kloset_duduk_jongkok": resolved_dual_kloset_count,
            "rejected_non_kos_rows": int(is_non_kos.sum()),
            "rejected_unlogical_price_rows": int((~valid_price).sum()),
            "rejected_unlogical_area_rows": int((~valid_area).sum()),
        },
        "quality_dimensions_before_after": {
            "completeness": {
                "raw_missing_cells": raw_missing_cells,
                "staging_missing_cells": int(canonical.isna().sum().sum()),
            },
            "validity": {
                "valid_numeric_rows": int(valid_numeric.sum()),
                "active_kos_rows": int(canonical["kos_aktif"].sum()),
                "accepted_for_analysis": int(canonical["accepted_for_analysis"].sum()),
            },
            "consistency": {
                "security_categories": sorted(canonical["keamanan_kos"].unique().tolist()),
                "bathroom_type_categories": sorted(canonical["tipe_kamar_mandi"].unique().tolist()),
                "parking_categories": sorted(canonical["lahan_parkir"].unique().tolist()),
                "night_rule_categories": sorted(canonical["aturan_jam_malam"].unique().tolist()),
                "floor_categories": sorted(canonical["kategori_lantai"].unique().tolist()),
            },
            "uniqueness": {
                "exact_duplicates": raw_exact_duplicates,
                "logical_duplicate_rows": int(canonical["duplicate_logis"].sum()),
                "unique_rows": int(len(canonical) - canonical["duplicate_logis"].sum()),
            },
        },
        "missing_cells_by_column": missing_after,
        "rejection_counts": canonical["rejection_reason"].value_counts().to_dict(),
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return canonical, report


if __name__ == "__main__":
    normalize_survey()
