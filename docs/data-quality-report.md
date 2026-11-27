# Data Quality Report

Laporan kualitas data utama untuk dataset survei kos Kabupaten Toba (`data/raw/Survey_Kos.csv`, 928 baris) didokumentasikan secara lengkap pada:

- [docs/laporan-kualitas-data.md](./laporan-kualitas-data.md) — Laporan lengkap pemeriksaan 4 dimensi kualitas data (*Completeness, Validity, Consistency, Uniqueness*), aturan normalisasi, duplikasi, outlier IQR, dan status `model_ready`.
- [data/quality/survey_quality_v1.json](../data/quality/survey_quality_v1.json) — Ringkasan metrik kualitas terstruktur hasil eksekusi `python etl/normalize_survey.py`.
