# Peta Tugas Issue dan Milestone (`da-ds-2026-kelompok-10`)

Dokumen ini menjadi panduan pembagian pekerjaan proyek terintegrasi **Data Analitik & Data Science** Kelompok 10.
Setiap pekerjaan mengikuti alur wajib:

```text
Issue -> branch anggota (develop-1..5) -> commit -> Pull Request ke develop -> review -> merge ke develop -> PR ke main
```

Tidak ada push langsung ke `main` atau `develop`. Setiap anggota wajib memiliki kontribusi yang di-merge pada sisi **Data Analitik (`DA`)** dan **Data Science (`DS`)**.

---

## 1. Status Milestone & Tag Checkpoint

| Milestone | Tag Rilis Wajib | Status | Fokus & Bukti Utama |
|---|---|---|---|
| **CP1 Proposal** | `v0.1-cp1` | **Selesai (100%)** | Proposal (`docs/proposal/proposal-proyek.md`), pertanyaan analitik, KPI, target pemodelan, dan pembagian peran (`#7`, `#8`, `#9`, `#10`). |
| **CP2 Data readiness** | `v0.2-cp2` | **Hampir Selesai (75%)** | Preprocessing 928 baris `Survey_Kos.csv` (`#11`, `#13`, `#14`, `#54` — Selesai), fitur kandidat (`#16` — Selesai), sisa finalisasi EDA 928 baris (`#15`) & laporan CP2 (`#17`). |
| **CP3 Checkpoint Tengah** | `v0.3-cp3` | **Sedang Berjalan** | Dashboard v1 terhubung warehouse survei (`#19`, `#27`, `#32`, `#37`, `#44`), perbandingan 4 model regresi & tuning (`#18`, `#29`, `#36`, `#38`), serta analisis fasilitas & jarak (`#20`, `#26`, `#30`, `#34`, `#43`, `#47`). |
| **CP4 Prototipe Terintegrasi** | `v0.4-cp4` | **Sedang Berjalan** | API prediksi & kalkulator harga (`#21`, `#31` — Selesai, `#35`, `#40`), klasifikasi harga wajar & simulasi fasilitas (`#22`, `#28`, `#33`, `#39`), pencarian kos (`#46`), storytelling (`#45`), dan ETL otomatis (`#42`). |
| **CP5 Presentasi Akhir** | `v1.0-final` | **Terjadwal** | Deployment URL publik & uji pengguna (`#58`), naskah jurnal (`#59`), finalisasi 10+ visualisasi advance (`#60`), reproducibility ML & model card (`#61`), serta laporan akhir & code freeze (`#62`). |

---

## 2. Pembagian Peran & Issue per Anggota (Lintas Lapisan DA & DS)

| Anggota | Akun GitHub | Branch Kerja | CP1 & CP2 | CP3 (Checkpoint Tengah) | CP4 (Prototipe Terintegrasi) | CP5 (Presentasi Akhir) | Cakupan Lapisan |
|---|---|---|---|---|---|---|---|
| **Samuel Bona Tua Hutagaol** (PM & Data/ML Engineer) | `Samuga-14` | `develop-1` | `#7`, `#8`, `#11`, `#13`, `#14`, `#54` (Closed) | Supervisi integrasi warehouse & review PR | `#22`, `#28` (#22-A), `#33` (#22-B), `#39` (#22-C), `#42` (#47), `#45` (#46) | `#62` (#CP5-E) | `DA`, `DS`, `Docs` |
| **Intan Sonia Siregar** (ML & API Engineer) | `intansrg30` | `develop-2` | `#16` (Closed) | Dukungan fitur kandidat & split 833 baris `model_ready` | `#21`, `#31` (#21-A, Closed), `#35` (#21-B), `#40` (#21-C) | `#58` (#CP5-A) | `DA`, `DS`, `Docs` |
| **Epelina Pangaribuan** (Data Analyst & Research) | `EpelinaPangaribuan` | `develop-3` | `#9` (Closed), `#15` | `#20`, `#26` (#20-A), `#30` (#20-B), `#34` (#20-C), `#43` (#44), `#47` (#43) | Kontribusi narasi temuan EDA untuk storytelling | `#59` (#CP5-B) | `DA`, `DS`, `Jurnal`, `Docs` |
| **Esthefany Christin Sipahutar** (ML Experiment & Eval) | `esthefanysipahutar` | `develop-4` | Review fitur & split data | `#18`, `#29` (#18-A), `#36` (#18-B), `#38` (#18-C) | Integrasi visualisasi evaluasi model ke dashboard | `#61` (#CP5-D) | `DA`, `DS`, `Docs` |
| **Novsiana Silalahi** (BI Warehouse & Viz) | `NovsianaSilalahi` | `develop-5` | `#10` (Closed), `#17` | `#19`, `#27` (#19-A, Closed), `#32` (#19-B), `#37` (#19-C), `#44` (#42) | `#46` (#45) | `#60` (#CP5-C) | `DA`, `DS`, `Docs` |

---

## 3. Ringkasan Hasil Preprocessing Terbaru (Issue #11, #14, & #54 — Selesai)

- **Status:** Merged ke `develop` (PR #56) dan `main` (PR #57).
- **Dataset Mentah Utama:** `data/raw/Survey_Kos.csv` (**928 baris**, **35 kolom** — memenuhi syarat $\ge 500$ baris data primer).
- **Dataset Staging Bersih:** `data/staging/survey_clean_v1.csv` (**928 baris**, **74 kolom**, **0 sel kosong**).
- **Exact Duplicate:** `0` baris.
- **Duplikasi Logis (`duplicate_logis`):** `42` baris terlibat (886 baris unik murni).
- **Kandidat Outlier IQR (`price_anomaly_iqr`):** `42` baris (Batas bawah: `Rp229.687,50` | Batas atas: `Rp1.142.187,50`).
- **Lolos Analisis Dasar & Dimuat ke Warehouse (`accepted_for_analysis = 1`):** **923 baris** pada `fact_sewa_kos` di `data/tobakost_survey_warehouse.db`.
- **Siap Pemodelan Baseline (`model_ready = 1`):** **833 baris**.
- **Unit Test Preprocessing (`tests/test_normalize_survey.py`):** **8 passed (OK)**.

---

## 4. Urutan Langkah Kerja Berikutnya (Next Steps Setelah Preprocessing)

Setelah preprocessing 928 baris selesai, urutan langkah tim adalah:

```text
1. Finalisasi CP2 (Issue #15 & #17) -> Buat Tag v0.2-cp2
        ↓
2. Update Split 833 baris model_ready & Latih 4 Model Regresi + Tuning CV (Issue #18: #29, #36, #38)
   [Berjalan paralel dengan:]
   - Integrasi Dashboard v1 ke Warehouse Survei 923 baris (Issue #19: #32, #37, #44)
   - Analisis Pengaruh Fasilitas & Aksesibilitas Jarak Meter (Issue #20: #26, #30, #34, #43, #47)
        ↓
3. Demo Tengah CP3 -> Buat Tag v0.3-cp3
        ↓
4. Integrasi API Prediksi, Kalkulator Harga, Klasifikasi Harga Wajar, Simulasi Fasilitas, & Storytelling (Issue #21, #22, #42, #45, #46) -> Buat Tag v0.4-cp4
        ↓
5. Deployment ke URL Publik, Uji Pengguna, Finalisasi Naskah Jurnal, & Laporan Akhir (Issue #58..#62) -> Buat Tag v1.0-final
```
