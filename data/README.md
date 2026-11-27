# Data (`da-ds-2026-kelompok-10`)

Folder ini menyimpan sumber data mentah (`raw/`), data hasil pembersihan & normalisasi (`staging/`), laporan kualitas data terstruktur (`quality/`), pembagian train/test split (`split_ids.csv`), serta database SQLite Star Schema Data Warehouse.

## Daftar Dataset & File Utama Saat Ini

| Path File | Baris & Kolom | Peran / Keterangan |
|---|---|---|
| `data/raw/Survey_Kos_Fix.csv` | **569 baris, 35 kolom** | **Sumber data primer utama terbaru** hasil kurasi survei Google Form Kos Kabupaten Toba ($\ge 500$ baris data primer; tidak boleh diedit/ditimpa oleh ETL). |
| `data/raw/Survey_Kos.csv` | 928 baris, 35 kolom | Arsip dataset survei versi sebelumnya. |
| `data/raw/data_fix.csv` | 328 baris, 44 kolom | Arsip batch awal survei. |
| `data/staging/survey_clean_v1.csv` | **569 baris, 74 kolom** | Output staging bersih hasil `python etl/normalize_survey.py` (0 sel kosong, jarak dalam meter `_m`, 7 kolom `klasifikasi_jarak_*`, `kategori_lantai`, pembersihan logis ketat, dan flag kualitas). |
| `data/quality/survey_quality_v1.json` | JSON Report | Ringkasan metrik 4 dimensi kualitas data (*Completeness, Validity, Consistency, Uniqueness*), tindakan pembersihan logis, batas IQR (`Rp175.000` – `Rp1.175.000`), `accepted_for_analysis` (**556 baris**), dan `model_ready` (**485 baris**). |
| `data/tobakost_survey_warehouse.db` | **556 baris fact** | SQLite Star Schema Data Warehouse survei riil yang dibangun oleh `python etl/run_survey_star_schema.py` (disinkronkan juga ke `data/tobakost_warehouse.db`). |
| `data/split_ids.csv` | CSV Split | Menyimpan pembagian ID unit kos (`train` 80% / `test` 20% dengan `random_state=42`) agar eksperimen model seluruh anggota tim 100% reproducible. |

## Cara Menjalankan Pipeline Data Survei (Reproducible)

```powershell
python etl/normalize_survey.py
python etl/run_survey_star_schema.py
python -m unittest discover -s tests -v
```

## Dokumentasi Terkait
- [docs/data-dictionary.md](../docs/data-dictionary.md) — Kamus data lengkap seluruh kolom staging, satuan, dan aturan normalisasi.
- [docs/laporan-kualitas-data.md](../docs/laporan-kualitas-data.md) — Laporan pemeriksaan kualitas data sebelum dan sesudah preprocessing ketat.
- [docs/laporan-eda.md](../docs/laporan-eda.md) — Laporan Exploratory Data Analysis (EDA) dan 5 temuan utama pada survei kos Kabupaten Toba.
