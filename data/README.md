# Data

`sample/` berisi sampel kecil yang boleh di-commit. Data lengkap disimpan di lokasi yang
disetujui tim dan ditautkan di dokumen ini, bukan di repository jika melebihi 50 MB atau
mengandung data sensitif.

## Data saat ini

- Dataset dummy aktif: `raw/dummy_baru.csv` jika `TOBAKOST_SOURCE_CSV` diarahkan ke
  file tersebut; dataset lama `../data/dummy_data_gform_kos_toba_600.csv` tetap menjadi
  fallback.
- Dataset survei nyata `raw/data_fix.csv` diproses dengan
  `python etl/normalize_survey.py` dan tidak boleh diedit atau ditimpa.
- Output staging: `data/staging/survey_clean_v1.csv`.
- Laporan kualitas: `data/quality/survey_quality_v1.json`.
- Warehouse survei terpisah: `python etl/run_survey_star_schema.py`
  menghasilkan `data/tobakost_survey_warehouse.db`. Warehouse dummy lama tidak ditimpa.
- ETL menormalisasi ekspor Google Form baru ke schema kanonik tanpa mengubah file di `raw/`.
- Warehouse dummy lokal dibuat ulang oleh `python etl/run_etl_star_schema.py` dan tidak
  disimpan di Git.
- Data riil nantinya masuk ke `raw/` dan tidak boleh ditimpa oleh ETL.

Tambahkan sumber, tanggal pengambilan, lisensi/izin, checksum, dan pemilik data setiap kali
dataset baru masuk.
