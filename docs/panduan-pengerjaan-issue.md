# Panduan Lengkap Pengerjaan Issue, Instruksi Teknis, Lokasi File, Output, & Clue (`da-ds-2026-kelompok-10`)

Dokumen ini adalah **buku panduan teknis lengkap** untuk seluruh anggota **Kelompok 10** dalam menyelesaikan setiap Issue pada Milestone **CP2 (`v0.2-cp2`)**, **CP3 (`v0.3-cp3`)**, **CP4 (`v0.4-cp4`)**, hingga **CP5 (`v1.0-final`)** berdasarkan dataset primer terbaru `data/raw/Survey_Kos_Fix.csv` (**569 baris raw** $\rightarrow$ **556 baris warehouse** $\rightarrow$ **485 baris `model_ready`**).

---

## 0. Aturan Emas & Alur Kerja Git (Wajib Dipatuhi Seluruh Anggota)

1. **Jangan pernah commit atau push langsung ke `main` atau `develop`!**
2. **Gunakan branch kerja masing-masing:**
   - **Samuel (`@Samuga-14`):** `develop-1`
   - **Intan (`@intansrg30`):** `develop-2`
   - **Epelina (`@EpelinaPangaribuan`):** `develop-3`
   - **Esthefany (`@esthefanysipahutar`):** `develop-4`
   - **Novsiana (`@NovsianaSilalahi`):** `develop-5`
3. **Langkah pertama sebelum mulai mengerjakan Issue (Sinkronisasi Data Terbaru):**
   ```powershell
   git checkout develop-<nomor_branch_kamu>
   git checkout -- data/staging/survey_clean_v1.csv
   git pull origin main
   ```
4. **Setelah selesai mengerjakan Issue:**
   ```powershell
   git add <file_yang_kamu_kerjakan>
   git commit -m "feat/docs/data: deskripsi singkat pekerjaan (Closes #<nomor_issue>)"
   git push origin develop-<nomor_branch_kamu>
   ```
   Lalu buka GitHub $\rightarrow$ buat **Pull Request (PR)** dari `develop-<nomor>` ke **`develop`** $\rightarrow$ minta **1 teman sekelompok me-review & approve PR** sebelum di-merge!

---

## 1. Milestone: `CP2 Data readiness` (Target Tag: `v0.2-cp2`)

### Issue `#71` (`#CP2-A`) — `data: preprocessing ulang & data cleaning logis ketat pada Survey_Kos_Fix.csv (569 baris)`
- **Assignee:** `@Samuga-14` (`develop-1`) | **Label:** `DA`, `DS`, `Docs` | **Status:** `CLOSED (Selesai)`
- **Deskripsi:** Melakukan preprocessing dan pembersihan logis ketat pada `data/raw/Survey_Kos_Fix.csv` (569 baris, 35 kolom) tanpa menyentuh file raw.
- **Lokasi Pengerjaan:** `etl/normalize_survey.py`, `etl/run_survey_star_schema.py`, `tests/test_normalize_survey.py`.
- **Output yang Dihasilkan:**
  - `data/staging/survey_clean_v1.csv` (**569 baris, 74 kolom, 0 sel kosong**).
  - `data/quality/survey_quality_v1.json` (audit 4 dimensi kualitas data & rincian tindakan cleaning logis).
  - `data/tobakost_survey_warehouse.db` & `data/tobakost_warehouse.db` (**556 baris `fact_sewa_kos`**).

---

### Issue `#15` (`#CP2-B`) — `EDA ulang & visualisasi kualitas data 4 dimensi pada Survey_Kos_Fix.csv (569 baris)`
- **Assignee:** `@EpelinaPangaribuan` (`develop-3`) | **Label:** `DA`, `Docs` | **Milestone:** `CP2 Data readiness`
- **Deskripsi:**
  Menyusun Exploratory Data Analysis (EDA) dan visualisasi pemeriksaan 4 dimensi kualitas data (*Completeness, Validity, Consistency, Uniqueness*) sebelum vs sesudah preprocessing ketat pada dataset `Survey_Kos_Fix.csv` (**569 baris raw $\rightarrow$ 556 baris `accepted_for_analysis`**).
- **Lokasi Pengerjaan (File yang Diedit/Dijalankan):**
  1. `notebooks/01_profiling_survey.ipynb` (Notebook profiling kualitas data raw vs staging).
  2. `notebooks/02_eda_survey.ipynb` (Notebook visualisasi distribusi harga, kecamatan, luas kamar, fasilitas, dan jarak meter).
  3. `docs/laporan-eda.md` (Dokumen laporan 5 temuan utama EDA).
- **Cara Pengerjaan (Step-by-Step):**
  1. Buka `notebooks/01_profiling_survey.ipynb`, pastikan path membaca `../data/raw/Survey_Kos_Fix.csv` (569 baris) dan `../data/staging/survey_clean_v1.csv`, lalu klik **Run All** agar output sel ter-update.
  2. Buka `notebooks/02_eda_survey.ipynb`, filter data dengan `df[df["accepted_for_analysis"] == 1]` (**556 baris**), lalu buat/jalankan grafik:
     - Histogram & Boxplot `harga_bulanan_norm` (Median: **Rp675.000**, Mean: **Rp689.075**, Q1: **Rp550.000**, Q3: **Rp800.000**, Batas IQR: **Rp175.000 – Rp1.175.000**).
     - Bar chart perbandingan median harga sewa lintas **16 Kecamatan** dan **Kategori Penghuni** (`Campur` Rp700rb, `Putri` Rp700rb, `Putra` Rp575rb).
     - Perbandingan harga berdasarkan `kategori_lantai` (`1`, `2`, `3`, `4 - 5`) dan luas kamar (`luas_kamar_m2`, median **12,0 $\text{m}^2$**).
  3. Cek dan rapikan narasi di `docs/laporan-eda.md`.
- **Output yang Wajib Ada:**
  - Notebook `01_profiling_survey.ipynb` dan `02_eda_survey.ipynb` dengan output grafik yang sudah ter-render untuk 569/556 baris.
  - Dokumen `docs/laporan-eda.md` yang memuat 5 temuan utama EDA.
- **Clue & Tips Penting:**
  - Gunakan angka ringkasan dari `data/quality/survey_quality_v1.json`: sel kosong turun dari **50 sel $\rightarrow$ 0 sel**, imputasi jarak laundry `0` m = **13 baris**, resolusi kontradiksi `Kamar Kosong` = **3 baris**, resolusi dual kloset = **5 baris**, dan outlier IQR = **28 baris**.
  - Gunakan **median** (bukan mean) saat membandingkan harga antar-kecamatan karena distribusi harga miring ke kanan (*right-skewed*).

---

### Issue `#16` (`#CP2-C`) — `Seleksi fitur kandidat & sinkronisasi train/test split (485 baris model_ready)`
- **Assignee:** `@intansrg30` (`develop-2`) | **Label:** `DA`, `DS` | **Milestone:** `CP2 Data readiness`
- **Deskripsi:**
  Menentukan daftar fitur kandidat prediktor harga sewa kos bulanan (`harga_bulanan_norm`) dan menyinkronkan pembagian data latih/uji (`data/split_ids.csv`, rasio 80:20, `random_state=42`) pada subset bersih **`model_ready = 1` (485 baris)**.
- **Lokasi Pengerjaan (File yang Diedit/Dicek):**
  1. `models/features_candidate.py` (Definisi fitur kandidat dari tabel staging/mart).
  2. `models/features.py` (Konfigurasi `FEATURE_COLUMNS`, `NUMERIC_FEATURES`, `CATEGORICAL_FEATURES`).
  3. `data/split_ids.csv` (File ID pembagian `train` dan `test`).
- **Cara Pengerjaan (Step-by-Step):**
  1. Cek `models/features.py` dan `models/features_candidate.py`, pastikan fitur yang digunakan mencakup:
     - **Spesifikasi Kamar:** `luas_kamar_m2`, `jumlah_lantai`, `ac_non_ac`, `tipe_kamar_mandi`, `fasilitas`, `skor_kelengkapan_fasilitas`.
     - **Lokasi & Aksesibilitas:** `kecamatan`, `jarak_ke_kampus_kantor_sekolah_terdekat_km`, `jarak_ke_pasar_km`, `jarak_krusial_km`, `jarak_ibadah_m`, `jarak_ke_jalan_raya_m`, `indeks_aksesibilitas_lokasi`.
     - **Aturan & Kontrak:** `kategori_penghuni`, `wifi_non_wifi`, `sumber_air_utama`, `dapur`, `lahan_parkir`, `keamanan_kos`, `aturan_jam_malam_masuk`, `skema_biaya_listrik`, `sewa_tahunan_bulanan`.
  2. Verifikasi `data/split_ids.csv` berisi tepat **485 baris** (`388 train`, `97 test`) dengan menjalankan:
     ```powershell
     python models/train_models.py
     ```
- **Output yang Wajib Ada:**
  - `models/features_candidate.py` & `models/features.py` yang bersih dan terdokumentasi docstring-nya.
  - `data/split_ids.csv` (485 baris `model_ready`).
- **Clue & Tips Penting:**
  - Jangan pernah memasukkan kolom `harga_sewa` ke dalam fitur prediktor karena akan menyebabkan **data leakage** terhadap target `harga_bulanan_norm`!

---

### Issue `#17` (`#CP2-D`) — `Sinkronisasi data dictionary, laporan kualitas data, dan star schema warehouse 556 baris`
- **Assignee:** `@NovsianaSilalahi` (`develop-5`) | **Label:** `DA`, `Docs` | **Milestone:** `CP2 Data readiness`
- **Deskripsi:**
  Merapikan dokumentasi kamus data (`docs/data-dictionary.md`), laporan kualitas data (`docs/laporan-kualitas-data.md`), serta memverifikasi skema bintang (`warehouse/ddl/star_schema.sql` & `warehouse/erd/star_schema.mmd`) terhadap database `data/tobakost_survey_warehouse.db` (**556 baris `fact_sewa_kos`**).
- **Lokasi Pengerjaan (File yang Diedit/Dicek):**
  1. `docs/data-dictionary.md`
  2. `docs/laporan-kualitas-data.md`
  3. `warehouse/ddl/star_schema.sql` & `warehouse/erd/star_schema.mmd`
- **Cara Pengerjaan (Step-by-Step):**
  1. Periksa `docs/data-dictionary.md` dan pastikan seluruh 74 kolom `data/staging/survey_clean_v1.csv` (termasuk 7 kolom `jarak_*_m`, 7 kolom `klasifikasi_jarak_*`, `kategori_lantai`, dan aturan validasi domain ketat $4\text{–}36\text{ m}^2$ serta $\text{Rp}150\text{rb–Rp}5\text{jt}$) tertulis lengkap.
  2. Jalankan `python etl/run_survey_star_schema.py` untuk memastikan keempat tabel dimensi (`dim_lokasi`, `dim_spesifikasi_kamar`, `dim_fasilitas_aturan`, `dim_kontrak_sewa`), tabel fakta (`fact_sewa_kos` = 556 baris), dan view `vw_mart_kos_lengkap` terbentuk tanpa error.
- **Output yang Wajib Ada:**
  - `docs/data-dictionary.md` dan `docs/laporan-kualitas-data.md` yang mutakhir untuk 569 baris `Survey_Kos_Fix.csv`.
  - Bukti verifikasi SQLite Star Schema (556 baris fact, 0 orphan foreign key).
- **Clue & Tips Penting:**
  - Cek jumlah baris tiap tabel dimensi dengan query SQLite sederhana atau lewat `etl/run_survey_star_schema.py`.

---

## 2. Milestone: `CP3 Checkpoint Tengah` (Target Tag: `v0.3-cp3`)

### Issue `#18` (`#CP3-ML`, beserta Sub-Issue `#29`, `#36`, `#38`) — `Eksperimen & perbandingan 4 model regresi harga sewa kos (485 baris model_ready)`
- **Assignee:** `@esthefanysipahutar` (`develop-4`) | **Label:** `DA`, `DS`, `Docs` | **Milestone:** `CP3 Checkpoint Tengah`
- **Rincian Sub-Issue:**
  - **`#29` (`#18-A`):** Melatih baseline **Linear Regression** dan **Ridge Regression (L2 Tuned)**.
  - **`#36` (`#18-B`):** Melatih & melakukan *hyperparameter tuning* 5-Fold Cross-Validation pada **Random Forest Regressor** dan **Gradient Boosting Regressor**.
  - **`#38` (`#18-C`):** Melakukan *error analysis* (analisis residual & *feature importance*) serta memperbarui `models/model_card.md`.
- **Lokasi Pengerjaan (File yang Diedit/Dijalankan):**
  1. `models/train_models.py` (Script training, 5-fold CV tuning, dan evaluasi 4 model).
  2. `models/metrics_summary.json` (Output metrik `MAE`, `RMSE`, `MAPE`, $R^2$ keempat model).
  3. `models/model_card.md` (Dokumentasi perbandingan model, *feature importance*, dan batasan model).
  4. `notebooks/03_baseline_regression.ipynb` (Notebook eksperimen & visualisasi residual/prediksi vs aktual).
- **Cara Pengerjaan (Step-by-Step):**
  1. Jalankan `python models/train_models.py` yang akan membaca **485 baris `model_ready = 1`** dari warehouse dan menggunakan split `data/split_ids.csv` (80% train = 388 baris, 20% test = 97 baris).
  2. Catat hasil perbandingan 4 model di `models/metrics_summary.json` dan `models/model_card.md`:
     - **Linear Regression (Baseline):** Test $R^2 = 0,7533$ | MAE = $\text{Rp}69.911$
     - **Ridge Regression (L2 Tuned):** Test $R^2 = 0,7522$ | MAE = $\text{Rp}70.191$
     - **Random Forest Regressor (Tuned — Model Terbaik):** Test $R^2 = 0,7967$ | MAE = $\text{Rp}65.590$
     - **Gradient Boosting Regressor (Tuned):** Test $R^2 = 0,7750$ | MAE = $\text{Rp}67.634$
  3. Lakukan *error analysis* di `models/model_card.md`: jelaskan mengapa Random Forest unggul (mampu menangkap interaksi non-linear antara fasilitas AC/Wi-Fi/kamar mandi dalam dengan klaster lokasi kecamatan) dan pada segmen kos mana error prediksi cenderung lebih tinggi.
- **Output yang Wajib Ada:**
  - `models/best_rf_model.pkl`, `models/metrics_summary.json`, `models/registry/manifest.json`, dan `models/model_card.md`.
- **Clue & Tips Penting:**
  - Saat menutup sub-issue lewat PR, kamu bisa mencantumkan `(Closes #29, Closes #36, Closes #38, Closes #18)` atau mengerjakan bertahap per sub-issue agar riwayat commit di `develop-4` terlihat sangat rapi dan terstruktur!

---

### Issue `#19` (`#CP3-BI`, beserta Sub-Issue `#27`, `#32`, `#37`, `#44`) — `Integrasi Dashboard v1 dengan Star Schema Warehouse Survei (556 baris fact)`
- **Assignee:** `@NovsianaSilalahi` (`develop-5`) | **Label:** `DA`, `Docs` | **Milestone:** `CP3 Checkpoint Tengah`
- **Rincian Sub-Issue:**
  - **`#27` (`#19-A` — Closed):** Membuat service ringkasan KPI dashboard.
  - **`#32` (`#19-B`):** Membuat filter global dashboard (`kecamatan`, `kategori_penghuni`, `jenis_kos`, `ac_non_ac`, `tipe_kamar_mandi`, rentang harga).
  - **`#37` (`#19-C`):** Membuat komponen visualisasi dashboard & penanganan *empty state* (ketika hasil filter = 0 unit kos).
  - **`#44` (`#42`):** Menganalisis & memvisualisasikan distribusi serta hierarki harga kos per kecamatan dan tipe kamar.
- **Lokasi Pengerjaan (File yang Diedit/Dicek):**
  1. `services/analytics_service.py` (Fungsi query agregasi KPI, distribusi harga, dan filter warehouse).
  2. `backend/api/http.py` (Endpoint `/api/summary`, `/api/analytics`, `/api/kos`).
  3. `frontend/app.js`, `frontend/index.html`, `frontend/styles.css` (Tampilan kartu KPI, filter interaktif, chart distribusi harga, dan *empty state*).
- **Cara Pengerjaan (Step-by-Step):**
  1. Pastikan `server_config.py` dan `services/analytics_service.py` membaca dari warehouse survei aktif (`556 baris` `vw_mart_kos_lengkap`).
  2. Uji filter kombinasi di frontend: pastikan saat user memilih filter yang tidak memiliki data, muncul pesan *empty state* yang informatif (bukan chart kosong/error JS).
  3. Pastikan KPI utama menampilkan **Total Unit Valid (`556`)**, **Median Tarif Bulanan (`Rp675.000`)**, **Rata-rata Tarif (`Rp689.075`)**, dan **Rentang IQR (`Rp550.000 – Rp800.000`)**.
- **Output yang Wajib Ada:**
  - Dashboard halaman Ringkasan & Distribusi Harga yang terhubung langsung ke 556 baris warehouse survei beserta penanganan *empty state*.
- **Clue & Tips Penting:**
  - Jalankan `python app.py` untuk menguji dashboard secara lokal di browser.

---

### Issue `#20` (`#CP3-EDA`, beserta Sub-Issue `#26`, `#30`, `#34`, `#43`, `#47`) — `Analisis pengaruh fasilitas kamar, keamanan, dan jarak meter terhadap tarif kos`
- **Assignee:** `@EpelinaPangaribuan` (`develop-3`) | **Label:** `DA`, `DS`, `Docs` | **Milestone:** `CP3 Checkpoint Tengah`
- **Rincian Sub-Issue:**
  - **`#26` (`#20-A`):** Menganalisis pengaruh fasilitas dalam kamar (AC, Wi-Fi, Kamar Mandi Dalam, Furnitur) terhadap kenaikan tarif bulanan.
  - **`#30` (`#20-B`):** Menganalisis hubungan 7 jarak fasilitas (dalam satuan meter `_m`) dan `klasifikasi_jarak_*` terhadap harga sewa.
  - **`#34` (`#20-C`):** Menyusun laporan temuan fasilitas & aksesibilitas di `docs/laporan-eda.md`.
  - **`#43` (`#44`):** Membangun pemetaan spasial (peta sebaran kos 16 kecamatan Kabupaten Toba) dan korelasi aksesibilitas.
  - **`#47` (`#43`):** Menganalisis kelengkapan fasilitas bersama dan tingkat keamanan kos (`Tidak Ada`, `CCTV`, `Penjaga/Satpam`, `Penjaga & CCTV`).
- **Lokasi Pengerjaan (File yang Diedit/Dicek):**
  1. `notebooks/02_eda_survey.ipynb`
  2. `docs/laporan-eda.md`
  3. `services/analytics_service.py` & `frontend/app.js` (Tab Analisis Fasilitas, Keamanan, & Peta Spasial Aksesibilitas).
- **Cara Pengerjaan (Step-by-Step):**
  1. Dokumentasikan dan visualisasikan selisih median harga fasilitas pada 556 baris valid:
     - **AC vs Non-AC:** Median `Rp1.208.333` vs `Rp666.667` (**+Rp541.666/bulan**).
     - **Wi-Fi vs Non-Wi-Fi:** Median `Rp725.000` vs `Rp525.000` (**+Rp200.000/bulan**).
     - **Kamar Mandi Dalam vs Luar:** Median `Rp700.000` vs `Rp500.000` (**+Rp200.000/bulan**).
     - **Keamanan Kos:** `Tidak Ada` (`Rp575.000`) $\rightarrow$ `CCTV` (`Rp650.000`) $\rightarrow$ `Penjaga/Satpam` (`Rp775.000`) $\rightarrow$ `Penjaga & CCTV` (`Rp850.000`).
  2. Dokumentasikan korelasi Spearman ($\rho$) jarak meter, khususnya **`jarak_jalan_raya_m` ($\rho = -0,2385$)** yang menunjukkan semakin dekat ke jalan raya utama, harga kos semakin tinggi.
- **Output yang Wajib Ada:**
  - Analisis lengkap & visualisasi pengaruh fasilitas, keamanan, serta aksesibilitas jarak meter di notebook, `docs/laporan-eda.md`, dan tab visualisasi dashboard.

---

## 3. Milestone: `CP4 Prototipe Terintegrasi` (Target Tag: `v0.4-cp4`)

### Issue `#21` (`#CP4-API`, beserta Sub-Issue `#31`, `#35`, `#40`) — `Integrasi API prediksi regresi & kalkulator estimasi harga kos`
- **Assignee:** `@intansrg30` (`develop-2`) | **Label:** `DA`, `DS` | **Milestone:** `CP4 Prototipe Terintegrasi`
- **Rincian Sub-Issue:**
  - **`#31` (`#21-A` — Closed):** Menyiapkan model artifact loader & validasi manifest (`tests/test_model_loader.py`).
  - **`#35` (`#21-B`):** Membuat endpoint prediksi `POST /api/predict` dan validasi input spesifikasi kamar/lokasi.
  - **`#40` (`#21-C`):** Mengintegrasikan form Kalkulator Estimasi Harga Kos di `frontend/app.js` & `frontend/index.html` dengan endpoint `/api/predict`.
- **Lokasi Pengerjaan:** `backend/api/http.py`, `models/registry/manifest.json`, `frontend/app.js`, `frontend/index.html`, `tests/test_model_loader.py`.
- **Cara Pengerjaan & Output:**
  - Pastikan endpoint `POST /api/predict` memvalidasi input (mis. `luas_kamar_m2` antara 4–36 $\text{m}^2$), memanggil bundle `models/best_rf_model.pkl`, dan mengembalikan estimasi harga bulanan beserta rentang kepercayaan ($\pm \text{MAE}$).
  - Jalankan `python -m unittest tests/test_model_loader.py -v` (11 unit tests wajib `OK`).

---

### Issue `#22` (`#CP4-SIM`, beserta Sub-Issue `#28`, `#33`, `#39`, `#42`, `#45`) — `Evaluasi kewajaran harga (Kemurahan/Wajar/Kemahalan) & simulasi upgrade fasilitas`
- **Assignee:** `@Samuga-14` (`develop-1`) | **Label:** `DA`, `DS`, `Docs` | **Milestone:** `CP4 Prototipe Terintegrasi`
- **Rincian Sub-Issue:**
  - **`#28` (`#22-A`):** Menentukan aturan klasifikasi harga wajar (`Kemurahan / Underpriced`, `Wajar / Fair Price`, `Kemahalan / Overpriced`) menggunakan ambang $\pm \max(15\%, \text{MAE model})$ di `services/analytics_service.py` (`classify_fair_price`).
  - **`#33` (`#22-B`):** Membuat mesin simulasi *what-if* penambahan fasilitas kamar (`simulate_facility_upgrades` & endpoint `POST /api/simulate-facilities`: simulasi tambah AC, Wi-Fi, Kamar Mandi Dalam, Kloset Duduk, Water Heater, Parkir Mobil, CCTV).
  - **`#39` (`#22-C`):** Mengintegrasikan rekomendasi harga wajar, simulasi fasilitas, dan unit test `tests/test_fair_price_simulation.py`.
  - **`#42` (`#47`):** Membangun pipeline ETL otomatis (`etl/normalize_survey.py` $\rightarrow$ `etl/run_survey_star_schema.py`) dan laporan kualitas JSON.
  - **`#45` (`#46`):** Menyusun modul *Data Storytelling* dan rekomendasi keputusan lokal bagi mahasiswa/pekerja & pemilik kos Kabupaten Toba (`get_storytelling_insights` & `/api/storytelling`).
- **Lokasi Pengerjaan:** `services/analytics_service.py`, `backend/api/http.py`, `tests/test_fair_price_simulation.py`, `docs/klasifikasi-harga-wajar.md`.

---

### Issue `#46` (`#45`) — `Membangun pencarian kos interaktif berbasis anggaran`
- **Assignee:** `@NovsianaSilalahi` (`develop-5`) | **Label:** `DA`, `DS` | **Milestone:** `CP4 Prototipe Terintegrasi`
- **Deskripsi:** Membangun fitur *Kos Finder* interaktif di dashboard yang memungkinkan mahasiswa/perantau mencari dan mengurutkan rekomendasi unit kos dari 556 baris warehouse berdasarkan batas anggaran bulanan (mis. $\le \text{Rp}700.000$), kecamatan tujuan, fasilitas wajib (Wi-Fi/Kamar Mandi Dalam), dan status kewajaran harga (`Kemurahan` / `Wajar`).
- **Lokasi Pengerjaan:** `services/analytics_service.py`, `backend/api/http.py`, `frontend/app.js`, `frontend/index.html`.
- **Output:** Tabel/kartu rekomendasi kos interaktif dengan lencana (*badge*) `Kemurahan`, `Wajar`, atau `Kemahalan` berdasarkan selisih harga aktual terhadap prediksi model.

---

## 4. Milestone: `CP5 Presentasi Akhir` (Target Tag: `v1.0-final`)

| No. Issue | Judul Issue | Assignee (Branch) | Lokasi Pengerjaan & Output Utama |
|---|---|---|---|
| **`#58` (`#CP5-A`)** | `Men-deploy aplikasi ke URL publik dan uji kegunaan pengguna` | **`@intansrg30`** (`develop-2`) | **Lokasi:** `Dockerfile` / `render.yaml` / konfigurasi hosting & `README.md`.<br>**Output:** URL publik yang bisa diakses dosen/penguji tanpa install lokal + ringkasan hasil uji kegunaan (*usability testing*) dari minimal 5 responden mahasiswa/pencari kos. |
| **`#59` (`#CP5-B`)** | `Menyusun lembar jurnal target dan finalisasi naskah jurnal ilmiah` | **`@EpelinaPangaribuan`** (`develop-3`) | **Lokasi:** `docs/journal/` (Lembar Jurnal Target SINTA/Scopus + Naskah Jurnal format IMRAD: *Introduction, Methods, Results and Discussion*).<br>**Output:** Draft paper ilmiah lengkap yang memuat metodologi Star Schema + perbandingan 4 model regresi pada 556/485 data survei kos Kabupaten Toba. |
| **`#60` (`#CP5-C`)** | `Finalisasi 10+ visualisasi advance, KPI pembanding, dan UI freeze` | **`@NovsianaSilalahi`** (`develop-5`) | **Lokasi:** `frontend/app.js`, `frontend/index.html`, `frontend/styles.css`.<br>**Output:** Minimal 10 visualisasi interaktif analitik & evaluasi ML yang responsif, konsisten tema warnanya, dan bebas bug UI (*UI Freeze*). |
| **`#61` (`#CP5-D`)** | `Finalisasi reproducibility model, visualisasi evaluasi ML, dan model card` | **`@esthefanysipahutar`** (`develop-4`) | **Lokasi:** `models/train_models.py`, `models/model_card.md`, `models/metrics_summary.json`.<br>**Output:** Kepastian 100% *reproducible training* (`random_state=42`), plot *Actual vs Predicted*, *Residual Distribution*, dan *Feature Importance* di dashboard & laporan. |
| **`#62` (`#CP5-E`)** | `Finalisasi laporan mingguan, laporan akhir, code freeze, dan tag rilis v1.0-final` | **`@Samuga-14`** (`develop-1`) | **Lokasi:** `README.md`, `docs/issue-task-map.md`, seluruh dokumen `docs/`.<br>**Output:** Audit akhir seluruh PR anggota, *code freeze* di `develop` $\rightarrow$ `main`, dan pembuatan Git Tag resmi `v0.2-cp2`, `v0.3-cp3`, `v0.4-cp4`, hingga `v1.0-final`. |
