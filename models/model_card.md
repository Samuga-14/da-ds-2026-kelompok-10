# Model Card — Prediksi Harga Sewa Kos Kabupaten Toba

## 1. Tujuan & Cakupan Penggunaan

Model ini memprediksi **tarif sewa kos ekuivalen bulanan (`harga_bulanan_norm` dalam Rupiah/bulan)** di Kabupaten Toba berdasarkan spesifikasi ukuran kamar, posisi lantai, fasilitas kamar & kamar mandi, sistem keamanan, skema pembayaran, dan jarak aksesibilitas lokasi.

Hasil prediksi model digunakan pada aplikasi TobaKost untuk tiga fungsi utama:
1. **Kalkulator Estimasi Harga Sewa (`POST /api/predict`):** Membantu calon penyewa dan pemilik kos mengetahui estimasi harga pasar bulanan dan tahunan beserta rentang toleransi $\pm\text{MAE}$.
2. **Evaluasi & Klasifikasi Kewajaran Harga (`classify_fair_price` & `enrich_price_analysis` — Issue #22 / #28):** Mengklasifikasikan unit kos berdasarkan persentase selisih harga aktual terhadap prediksi model (`selisih_persen = (harga_aktual - prediksi) / prediksi * 100%`) dengan ambang batas (**threshold**) **$\pm 6,0\%$**:
   - **`Underpriced (Sangat Hemat)` (`murah`):** `selisih_persen < -6,0%` (tarif aktual lebih murah $>6\%$ dari estimasi model untuk spesifikasi setara).
   - **`Fair Price (Harga Wajar)` (`wajar`):** `-6,0% <= selisih_persen <= +6,0%` (tarif sesuai standar pasar Kabupaten Toba).
   - **`Overpriced (Kemahalan)` (`mahal`):** `selisih_persen > +6,0%` (tarif aktual di atas estimasi model; disarankan mengecek fasilitas non-standar atau melakukan negosiasi).
3. **Simulasi Penambahan Fasilitas (`simulate_facility_upgrades` & `POST /api/simulate` — Issue #22 / #33):** Mensimulasikan perubahan estimasi tarif bulanan apabila pemilik kos menambahkan fasilitas tertentu (seperti AC, Kamar Mandi Dalam, Wi-Fi, TV, Meja Belajar, Parkir Mobil, Dapur Pribadi, atau Keamanan Penjaga/CCTV).

---

## 2. Dataset Pelatihan & Preprocessing

- **Sumber Data Primer:** `data/raw/Survey_Kos.csv` (**928 baris**, **35 kolom**) hasil survei Google Form Kos Kabupaten Toba.
- **Staging & Warehouse:** `data/staging/survey_clean_v1.csv` (928 baris, 0 sel kosong) $\rightarrow$ `data/tobakost_survey_warehouse.db` (**923 baris** pada `fact_sewa_kos`).
- **Subset Pelatihan (`model_ready = 1`):** **833 baris** konservatif (kos aktif, harga masih berlaku, lolos validasi dasar, bukan kandidat outlier IQR `Rp229.687,50`–`Rp1.142.187,50`, dan bukan duplikasi logis).
- **Pembagian Data (*Train/Test Split*):** 80% Train (**666 baris**) / 20% Test (**167 baris**) dengan `random_state=42`, tersimpan secara reproducible di `data/split_ids.csv`.

---

## 3. Algoritma yang Dibandingkan & Fitur

Empat algoritma regresi dilatih pada urutan fitur kanonik yang sama (`models/features.py`):
1. **Linear Regression (Baseline)**
2. **Ridge Regression (L2 Tuned)**
3. **Random Forest Regressor (Tuned)**
4. **Gradient Boosting / XGBoost (Tuned)**

Artifact model disimpan secara lokal melalui `python models/train_models.py` dan dicatat beserta versi `scikit-learn` pada `models/registry/model_manifest.json` serta `models/metrics_summary.json`.

**Catatan:** isi keputusan akhir `is_tahunan` (kontrol vs hanya bulanan) setelah rapat tim.

## Interpretasi Analisis Kewajaran Harga

Dashboard analitik membandingkan `harga_bulanan_norm` dengan prediksi Random Forest (`pred_rf`). Selisih persentase dihitung dengan rumus:

`((harga_bulanan_norm - pred_rf) / pred_rf) * 100`

Kategori ditentukan menggunakan ambang 6%:
- Di bawah -6%: `Underpriced (Sangat Hemat)`.
- Dari -6% sampai +6%, termasuk batasnya: `Fair Price (Harga Wajar)`.
- Di atas +6%: `Overpriced (Kemahalan)`.

Kategori tersebut menunjukkan perbandingan harga aktual terhadap prediksi model, bukan bukti mutlak bahwa harga kos murah atau mahal di pasar. Model masih berbasis data dummy, sehingga hasilnya bersifat ilustratif dan perlu divalidasi dengan data riil.

**Perbedaan dengan kalkulator API:** analitik dashboard menggunakan prediksi Random Forest untuk menentukan label kewajaran, sedangkan kalkulator API menggunakan model terpilih berdasarkan MAE pada test set. Label analitik tidak sama dengan hasil atau rentang estimasi kalkulator API.
---

## 4. Keterbatasan & Etika Penggunaan (Limitations)

- **Bukan Klaim Kausalitas Mutlak:** Simulasi penambahan fasilitas (`POST /api/simulate`) menunjukkan perubahan prediksi kondisional model berdasarkan distribusi data survei Kabupaten Toba, bukan jaminan kenaikan harga kausal secara mutlak di lapangan.
- **Ketidakpastian Estimasi:** Setiap prediksi tunggal dilengkapi rentang ketidakpastian $\pm\text{MAE}$ (`range_min_rp` s.d. `range_max_rp`). Faktor mikro seperti kualitas bangunan fisik, ventilasi alami, atau negosiasi personal tidak sepenuhnya tertangkap dalam fitur tabular.
- **Kompatibilitas Runtime:** Bundle `.pkl` terikat pada versi `scikit-learn` saat pelatihan. Jika versi lingkungan berubah, jalankan `python models/train_models.py` untuk memperbarui bundle dan manifest.
