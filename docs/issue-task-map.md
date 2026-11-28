# Peta Tugas Issue dan Milestone (`da-ds-2026-kelompok-10`)

Dokumen ini menjadi panduan pembagian pekerjaan proyek terintegrasi **Data Analitik & Data Science** Kelompok 10 berdasarkan dataset survei primer terbaru `data/raw/Survey_Kos_Fix.csv` (**569 baris, 35 kolom**).
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
| **CP2 Data readiness** | `v0.2-cp2` | **Sedang Berjalan** | Preprocessing ulang & data cleaning logis ketat pada 569 baris `Survey_Kos_Fix.csv` oleh `Samuga-14` (`#71` — Selesai), dilanjutkan sinkronisasi EDA (`#15`), fitur kandidat & split 485 baris (`#16`), serta data dictionary & star schema 556 baris (`#17`) oleh anggota tim. |
| **CP3 Checkpoint Tengah** | `v0.3-cp3` | **Sedang Berjalan** | Dashboard v1 terhubung warehouse survei 556 baris (`#19`, `#27`, `#32`, `#37`, `#44`), perbandingan 4 model regresi & tuning pada 485 baris `model_ready` (`#18`, `#29`, `#36`, `#38`), serta analisis fasilitas & jarak meter (`#20`, `#26`, `#30`, `#34`, `#43`, `#47`). |
| **CP4 Prototipe Terintegrasi** | `v0.4-cp4` | **Terjadwal** | API prediksi & kalkulator harga (`#21`, `#31`, `#35`, `#40`), klasifikasi harga wajar & simulasi fasilitas (`#22`, `#28`, `#33`, `#39`), pencarian kos (`#46`), storytelling (`#45`), dan ETL otomatis (`#42`). |
| **CP5 Presentasi Akhir** | `v1.0-final` | **Terjadwal** | Deployment URL publik & uji pengguna (`#58`), naskah jurnal (`#59`), finalisasi 10+ visualisasi advance (`#60`), reproducibility ML & model card (`#61`), serta laporan akhir & code freeze (`#62`). |

---

## 2. Pembagian Peran & Issue Terbaru per Anggota (Lintas Lapisan DA & DS)

| Anggota | Akun GitHub | Branch Kerja | CP1 & CP2 (Data Readiness) | CP3 (Checkpoint Tengah) | CP4 (Prototipe Terintegrasi) | CP5 (Presentasi Akhir) | Label |
|---|---|---|---|---|---|---|---|
| **Samuel Bona Tua Hutagaol** (PM, Preprocessing & Data Cleaning Lead) | `Samuga-14` | `develop-1` | `#7`, `#8`, `#11`, `#13`, `#14`, `#54`, **`#71` (#CP2-A: Preprocessing & Cleaning Ketat `Survey_Kos_Fix.csv`)** | Supervisi integrasi warehouse 556 baris & review PR | `#22` (#CP4-SIM), `#28` (#22-A), `#33` (#22-B), `#39` (#22-C), `#42` (#47), `#45` (#46) | `#62` (#CP5-E) | `DA`, `DS`, `Docs` |
| **Epelina Pangaribuan** (Data Analyst & Research) | `EpelinaPangaribuan` | `develop-3` | `#9` (Closed), **`#15` (#CP2-B: EDA Ulang & Viz Kualitas 4 Dimensi 569 Baris)** | `#20` (#CP3-EDA), `#26` (#20-A), `#30` (#20-B), `#34` (#20-C), `#43` (#44), `#47` (#43) | Kontribusi narasi temuan EDA untuk storytelling | `#59` (#CP5-B) | `DA`, `DS`, `Jurnal`, `Docs` |
| **Intan Sonia Siregar** (ML Feature & API Engineer) | `intansrg30` | `develop-2` | **`#16` (#CP2-C: Seleksi Fitur Kandidat & Train/Test Split 485 Baris)** | Dukungan pipeline fitur kandidat & validasi split | `#21` (#CP4-API), `#31` (#21-A), `#35` (#21-B), `#40` (#21-C) | `#58` (#CP5-A) | `DA`, `DS`, `Docs` |
| **Novsiana Silalahi** (BI Warehouse & Dashboard Viz) | `NovsianaSilalahi` | `develop-5` | `#10` (Closed), **`#17` (#CP2-D: Sinkronisasi Data Dictionary & Star Schema 556 Baris)** | `#19` (#CP3-BI), `#27` (#19-A), `#32` (#19-B), `#37` (#19-C), `#44` (#42) | `#46` (#45) | `#60` (#CP5-C) | `DA`, `DS`, `Docs` |
| **Esthefany Christin Sipahutar** (ML Experiment & Eval) | `esthefanysipahutar` | `develop-4` | Review distribusi target & korelasi fitur | **`#18` (#CP3-ML)**, `#29` (#18-A: Linear & Ridge), `#36` (#18-B: RF & GBR Tuning), `#38` (#18-C: Error Analysis & Model Card) | Integrasi visualisasi evaluasi model ke dashboard | `#61` (#CP5-D) | `DA`, `DS`, `Docs` |

---

## 3. Ringkasan Hasil Preprocessing & Cleaning Ketat Terbaru (Issue #71 — `Samuga-14`)

- **Dataset Mentah Utama:** `data/raw/Survey_Kos_Fix.csv` (**569 baris**, **35 kolom** — memenuhi syarat $\ge 500$ baris data primer).
- **Dataset Staging Bersih:** `data/staging/survey_clean_v1.csv` (**569 baris**, **74 kolom**, **0 sel kosong**).
- **Tindakan Pembersihan Logis Ketat (`logical_cleaning_actions`):**
  1. **Standarisasi Nama & Entitas:** Menghapus spasi ganda (`'Kos  birong'` -> `'Kos Birong'`), memetakan placeholder ke `'Kos Tanpa Nama'`, dan menolak 1 baris non-kos (`'Bukan kos tapi rumah keluarga'`).
  2. **Evaluasi & Batas Ketat Luas Kamar (`4.0 <= luas_kamar_m2 <= 36.0` m²):** Menghitung perkalian dimensi (`4x4`, `3,5x5`, `4*3`), mengonversi input panjang 1 sisi $1,5 \le s \le 4,0\text{ m}$ (`'2'`, `'3'`, `'3 m2'`, `'3 meter'`, `'4 m'`) menjadi luas persegi $s^2$, mengoreksi typo `2000` -> `200`, dan menolak 7 baris luas bangunan/rumah utuh (`42`–`240` m²).
  3. **Imputasi Logis Jarak Fasilitas Eksternal `0` Meter:** Mengimputasi 13 baris `jarak_laundry_m = 0` m dengan median kecamatan setempat (sementara `0` m pada `jarak_jalan_raya_m` tetap dipertahankan sebagai kos di pinggir jalan raya).
  4. **Batas Ketat Tarif Bulanan (`Rp150.000 <= harga_bulanan_norm <= Rp5.000.000`):** Menolak 6 baris dengan harga bulanan tidak logis `< Rp150.000/bulan` (akibat salah pilih periode `Per Tahun` pada nominal bulanan).
  5. **Rekonsiliasi Fasilitas & Biaya Tambahan:** Menghapus label kontradiktif `'Kamar Kosong'` pada 3 baris berfurnitur, menyelesaikan 5 baris pilihan ganda `'Toilet duduk, Toilet Jongkok'` berdasarkan `km_dalam`, serta menyelaraskan `ada_biaya_tambahan` dengan `biaya_tambahan_rp`.
- **Lolos Analisis Dasar & Dimuat ke Warehouse (`accepted_for_analysis = 1`):** **556 baris** pada `fact_sewa_kos` di `data/tobakost_survey_warehouse.db` (masih $\ge 500$ baris valid).
- **Siap Pemodelan Baseline (`model_ready = 1`):** **485 baris** (Batas IQR: `Rp175.000` – `Rp1.175.000`).
- **Unit Testing (`unittest discover -s tests -v`):** **22 passed (OK)**.
