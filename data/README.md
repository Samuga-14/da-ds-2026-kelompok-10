# Data (`da-ds-2026-kelompok-10`)

Folder ini menyimpan sumber data mentah (`raw/`), data hasil pembersihan & normalisasi (`staging/`), laporan kualitas data terstruktur (`quality/`), pembagian train/test split (`split_ids.csv`), serta database SQLite Star Schema Data Warehouse.

## Daftar Dataset & File Utama Saat Ini

| Path File | Baris & Kolom | Peran / Keterangan |
|---|---|---|
| `data/raw/Survey_Kos.csv` | **928 baris, 35 kolom** | **Sumber data primer utama** hasil survei Google Form Kos Kabupaten Toba (tidak boleh diedit/ditimpa oleh ETL). |
| `data/raw/data_fix.csv` | 328 baris, 44 kolom | Arsip batch awal survei (seluruh barisnya telah tercakup di dalam `Survey_Kos.csv`). |
| `data/staging/survey_clean_v1.csv` | **928 baris, 74 kolom** | Output staging bersih hasil `python etl/normalize_survey.py` (0 sel kosong, jarak dalam meter `_m`, 7 kolom `klasifikasi_jarak_*`, `kategori_lantai`, dan flag kualitas). |
| `data/quality/survey_quality_v1.json` | JSON Report | Ringkasan metrik 4 dimensi kualitas data (*Completeness, Validity, Consistency, Uniqueness*), batas IQR (`Rp229.687,50` – `Rp1.142.187,50`), dan jumlah `model_ready` (**833 baris**). |
| `data/tobakost_survey_warehouse.db` | **923 baris fact** | SQLite Star Schema Data Warehouse survei riil yang dibangun oleh `python etl/run_survey_star_schema.py`. |
| `data/split_ids.csv` | CSV Split | Menyimpan pembagian ID unit kos (`train` 80% / `test` 20% dengan `random_state=42`) agar eksperimen model seluruh anggota tim 100% reproducible. |
| `data/dummy_data_gform_kos_toba_600.csv` | 600 baris, 36 kolom | Dataset dummy prototipe awal (dipakai oleh `etl/run_etl_star_schema.py` untuk `data/tobakost_warehouse.db`). |

## Cara Menjalankan Pipeline Data Survei (Reproducible)

```powershell
python etl/normalize_survey.py
python etl/run_survey_star_schema.py
python -m unittest tests/test_normalize_survey.py -v
```

## Dokumentasi Terkait
- [docs/data-dictionary.md](../docs/data-dictionary.md) — Kamus data lengkap seluruh kolom staging, satuan, dan aturan normalisasi.
- [docs/laporan-kualitas-data.md](../docs/laporan-kualitas-data.md) — Laporan pemeriksaan kualitas data sebelum dan sesudah preprocessing.
- [docs/laporan-eda.md](../docs/laporan-eda.md) — Laporan Exploratory Data Analysis (EDA) dan 5 temuan utama pada 928 baris survei.
