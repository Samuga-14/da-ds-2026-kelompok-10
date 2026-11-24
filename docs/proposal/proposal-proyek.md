# Proposal Proyek Terintegrasi Data Analitik & Data Science (CP1)

**Judul Proyek:**  
**Analisis Faktor Penentu Tarif dan Prediksi Harga Sewa Kos Menggunakan Algoritma Machine Learning Berdasarkan Spesifikasi Fasilitas dan Aksesibilitas Lokasi di Kabupaten Toba**

**Kelompok:** Kelompok 10 (`da-ds-2026-kelompok-10`)  
**Institusi:** Institut Teknologi Del — Semester Ganjil 2026/2027  
**Dosen Pengampu:** Oppir Hutapea, M.Kom

---

## 1. Latar Belakang & Rumusan Masalah

Pertumbuhan aktivitas pendidikan tinggi (seperti Institut Teknologi Del), perkantoran, serta kawasan pariwisata dan industri di Kabupaten Toba mendorong peningkatan permintaan hunian sewa (kos-kosan) di berbagai kecamatan seperti Laguboti, Balige, Porsea, dan Ajibata. Namun, penetapan harga sewa kos di Kabupaten Toba selama ini masih bersifat subjektif dan belum memiliki acuan standar yang transparan antara spesifikasi fasilitas, lokasi/aksesibilitas, dan tarif sewa bulanan.

Akibatnya:
1. **Calon penyewa (mahasiswa, pekerja, pelajar, keluarga)** kesulitan menilai apakah tarif suatu kamar kos tergolong murah (*underpriced*), wajar (*fair price*), atau kemahalan (*overpriced*) dibandingkan fasilitas dan jaraknya.
2. **Pemilik kos** belum memiliki indikator berbasis data untuk menentukan tarif sewa yang kompetitif maupun memperkirakan peningkatan nilai sewa apabila menambah fasilitas tertentu (seperti kamar mandi dalam, Wi-Fi, AC, atau perabot kamar).

---

## 2. Pengguna & Pengambil Keputusan (Target Users)

| Kelompok Pengguna | Kebutuhan Keputusan yang Didukung Aplikasi |
|---|---|
| **1. Pencari / Penyewa Kos** (Mahasiswa IT Del, Pekerja, Pelajar, Keluarga) | Mencari kos sesuai anggaran bulanan, membandingkan fasilitas dan jarak (meter) antar kecamatan/desa, serta mengecek kewajaran harga sewa sebelum menyewa. |
| **2. Pemilik / Pengelola Kos di Kabupaten Toba** | Menentukan harga sewa bulanan/tahunan yang wajar menggunakan kalkulator prediksi Machine Learning serta mensimulasikan dampak penambahan fasilitas terhadap tarif sewa. |
| **3. Pengelola Kampus / Pemangku Kebijakan Lokal** | Memahami peta sebaran tarif, ketersediaan fasilitas hunian, dan aksesibilitas tempat tinggal di sekitar kawasan pendidikan dan pusat ekonomi Kabupaten Toba. |

---

## 3. Pertanyaan Analitik (Sisi Data Analitik)

Dashboard visualisasi advance dirancang untuk menjawab 5 pertanyaan analitik utama:
1. **Ringkasan Tarif & Hunian (Section 1):** Bagaimana profil statistik tarif sewa ekuivalen bulanan (`harga_bulanan_norm` — rata-rata, median, IQR, minimum, maksimum) dan komposisi tipe kos lintas 16 kecamatan di Kabupaten Toba?
2. **Distribusi & Hierarki Harga (Section 2):** Bagaimana pola distribusi dan hierarki harga sewa kos jika di-drill-down berdasarkan kecamatan, desa/kelurahan, kategori penghuni (`Putra`, `Putri`, `Campur`), luas kamar (`luas_kamar_m2`), posisi lantai (`kategori_lantai`), dan periode pembayaran (`per bulan` vs `per tahun`)?
3. **Fasilitas & Keamanan (Section 3):** Seberapa besar perbedaan tarif median antara kos dengan spesifikasi fasilitas kamar (AC, kamar mandi dalam, kloset duduk, shower, water heater, dipan, kasur, lemari, meja belajar), utilitas (Wi-Fi, skema listrik, sumber air), dan sistem keamanan (`CCTV`, `Penjaga/Satpam`, `Penjaga & CCTV`, `Tidak Ada`)?
4. **Pemetaan Spasial & Aksesibilitas Jarak (Section 4):** Bagaimana korelasi antara jarak dalam satuan meter (`jarak_*_m` dan `klasifikasi_jarak_*`) menuju pusat aktivitas utama (`Kampus IT Del`, `Kantor`, `Sekolah`), pasar/minimarket, fasilitas kesehatan, laundry, tempat ibadah, pusat kota, dan jalan raya utama terhadap variasi harga sewa?
5. **Pencarian & Evaluasi Kewajaran Harga (Section 5 & 6):** Unit kos mana saja yang memberikan nilai manfaat (*value for money*) terbaik sesuai batasan anggaran dan preferensi fasilitas pengguna?

---

## 4. Key Performance Indicators (KPI Utama Dashboard)

Dashboard menampilkan minimal **4 Kartu KPI Utama dengan Pembanding**:
1. **Total Unit Kos Tervalidasi (`accepted_for_analysis`):** Jumlah unit kos aktif yang lolos pemeriksaan kualitas (dibandingkan terhadap total 928 responden survei mentah dan jumlah `model_ready`).
2. **Median Tarif Sewa Bulanan (`Rp/Bulan`):** Nilai tengah harga sewa ekuivalen bulanan (dibandingkan terhadap rata-rata tarif dan rentang kuartil IQR `Rp229.688` – `Rp1.142.188`).
3. **Rasio Kelengkapan Fasilitas Utama (`%`):** Persentase unit kos yang menyediakan fasilitas kunci (Kamar Mandi Dalam & Wi-Fi) dibandingkan terhadap rata-rata populasi Kabupaten Toba.
4. **Indeks Aksesibilitas & Proporsi Harga Wajar (`%`):** Persentase unit kos yang berada dalam kategori jarak `Sangat Dekat (<= 500 m)` / `Dekat (501 - 1000 m)` ke tujuan utama serta proporsi unit berstatus *Fair Price / Underpriced* menurut evaluasi model.

---

## 5. Tugas Pemodelan, Target, & Metrik Sukses (Sisi Data Science)

* **Jenis Tugas Pemodelan:** Prediksi / Regresi (*Supervised Regression*) pada data tabular terstruktur.
* **Variabel Target (`y`):** `harga_bulanan_norm` (tarif sewa kos ekuivalen bulanan dalam Rupiah; tarif tahunan dinormalisasi dengan dibagi 12).
* **Sumber & Ukuran Dataset:** Data primer survei Google Form Kos Kabupaten Toba (`data/raw/Survey_Kos.csv`) sebanyak **928 baris** dan **35 kolom** (menghasilkan **923 baris** fact warehouse dan **833 baris** subset konservatif `model_ready = 1`).
* **Kelompok Fitur Kandidat (`X`):**
  1. *Spesifikasi Ukuran & Lantai:* `luas_kamar_m2`, `jumlah_lantai` / `kategori_lantai`.
  2. *Fasilitas Kamar & Kamar Mandi (Biner):* `ac`, `km_dalam`, `kloset_duduk`, `ada_shower`, `ada_water_heater`, `ada_dipan`, `ada_kasur`, `ada_lemari`, `ada_meja_belajar`, `ada_tv`, `ada_cermin`, `ada_kulkas_pribadi`.
  3. *Fasilitas Bersama, Aturan, & Keamanan:* `is_wifi`, `listrik_termasuk`, `keamanan_kos` (`CCTV`, `Penjaga/Satpam`, `Penjaga & CCTV`), `lahan_parkir`, `aturan_jam_malam`, `fasilitas_dapur`, `sumber_air`.
  4. *Aksesibilitas Lokasi (Meter):* 7 fitur `jarak_*_m` beserta klasifikasi kedekatannya.
  5. *Wilayah & Kontrak:* `kecamatan`, `kategori_penghuni`, `kapasitas_kamar`, `area_tempat_makan`, dan variabel kontrol `sewa_tahunan`.
* **Algoritma yang Dibandingkan (Minimal 4 Model):**
  1. *Linear Regression (OLS)* — Baseline model.
  2. *Ridge Regression (L2 Regularized)* — Linear model dengan tuning parameter `alpha`.
  3. *Random Forest Regressor* — Model ensemble non-linear (*bagging*) dengan hyperparameter tuning.
  4. *Gradient Boosting Regressor* — Model ensemble lanjutan (*boosting*) dengan hyperparameter tuning.
* **Skema Validasi & Metrik Evaluasi:**
  * Pembagian data *train/test split* reproducible 80/20 (`random_state=42`) pada baris `model_ready`, ditambah evaluasi *5-Fold Cross-Validation* dan *Hyperparameter Tuning* (`GridSearchCV` / `RandomizedSearchCV`).
  * Metrik sukses: **MAE** (*Mean Absolute Error* dalam Rupiah — metrik utama pemilihan model), **RMSE** (*Root Mean Squared Error*), **MAPE** (*Mean Absolute Percentage Error*), dan **$R^2$** (*Coefficient of Determination*).

---

## 6. Pembagian Peran Anggota Kelompok 10

Setiap anggota berkontribusi lintas lapisan (**Data Analitik** dan **Data Science**) melalui branch kerja masing-masing:

| Anggota | Akun GitHub | Branch Kerja | Peran Utama & Tanggung Jawab Lintas Lapisan (DA + DS) |
|---|---|---|---|
| **Samuel Bona Tua Hutagaol** | `Samuga-14` | `develop-1` | **Project Manager & Data/ML Engineer:** Koordinasi timeline & laporan mingguan, pipeline preprocessing & normalisasi survei 928 baris (`#11`, `#14`, `#54`), ETL otomatis (`#42`), klasifikasi kewajaran harga & simulasi fasilitas (`#22`, `#28`, `#33`, `#39`), data storytelling (`#45`), dan rilis final (`#CP5-E`). |
| **Intan Sonia Siregar** | `intansrg30` | `develop-2` | **ML & API Integration Engineer:** Seleksi fitur kandidat & reproducible split (`#16`), model registry loader & prediction service (`#31`), endpoint REST API prediksi & validasi input (`#21`, `#35`), integrasi kalkulator prediksi ke frontend (`#40`), serta deployment aplikasi ke URL publik (`#CP5-A`). |
| **Epelina Pangaribuan** | `EpelinaPangaribuan` | `develop-3` | **Data Analyst & Research Lead:** EDA & visualisasi kualitas data survei (`#15`), analisis statistik pengaruh fasilitas & aksesibilitas jarak terhadap tarif (`#20`, `#26`, `#30`, `#34`, `#47`), pemetaan spasial & korelasi aksesibilitas (`#43`), serta penyusunan lembar jurnal target & naskah jurnal ilmiah (`#CP5-B`). |
| **Esthefany Christin Sipahutar** | `esthefanysipahutar` | `develop-4` | **ML Experiment & Evaluation Engineer:** Pelatihan baseline Linear & Ridge Regression (`#18`, `#29`), pelatihan & hyperparameter tuning Random Forest & Gradient Boosting (`#36`), error analysis residual, visualisasi hasil model (*Actual vs Predicted* & *Residual Plot*) di dashboard, serta penyusunan *Model Card* (`#38`, `#CP5-D`). |
| **Novsiana Silalahi** | `NovsianaSilalahi` | `develop-5` | **BI Warehouse & Dashboard Viz Engineer:** Dokumentasi data dictionary & laporan CP2 (`#17`), service ringkasan statistik & integrasi warehouse (`#19`, `#27`), filter global & visualisasi distribusi/hierarki harga (`#32`, `#37`, `#44`), pencarian kos interaktif berbasis anggaran & kewajaran harga model (`#46`), serta finalisasi 10+ visualisasi advance (`#CP5-C`). |
