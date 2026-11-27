# Laporan EDA Survei Kos Toba (`Survey_Kos_Fix.csv` — 569 Baris)

## 1. Identitas dan Cakupan Dataset

- **Dataset mentah utama:** `data/raw/Survey_Kos_Fix.csv` (**569 baris**, **35 kolom** — memenuhi syarat $\ge 500$ baris data primer)
- **Dataset staging bersih:** `data/staging/survey_clean_v1.csv` (**569 baris**, **74 kolom** kanonik, klasifikasi jarak, & flag kualitas, **0 sel kosong**)
- **Warehouse survei skema bintang:** `data/tobakost_survey_warehouse.db` (**556 baris** pada `fact_sewa_kos`)
- **Subset siap pemodelan (`model_ready = 1`):** **485 baris**
- **Notebook eksperimen:** `notebooks/01_profiling_survey.ipynb` dan `notebooks/02_eda_survey.ipynb`
- **Revisi laporan:** 27 November 2026

Harga sewa tahunan dinormalisasi menjadi setara bulanan (`harga_bulanan_norm = harga_sewa / 12`), sedangkan harga bulanan dipertahankan. Seluruh analisis eksploratif menggunakan subset valid `accepted_for_analysis = 1` (**556 baris** yang telah lolos validasi domain ketat: kamar kos aktif, luas kamar $4\text{–}36\text{ m}^2$, dan harga bulanan $\text{Rp}150.000\text{–}\text{Rp}5.000.000$), sementara seluruh 569 baris tetap tersimpan utuh beserta kolom `rejection_reason` di staging.

---

## 2. Distribusi Harga Bulanan Normalisasi (`harga_bulanan_norm`)

Pada **556 baris** unit kos yang lolos validasi dasar dan domain logis:
- **Median:** **Rp675.000 / bulan**
- **Rata-rata (Mean):** **Rp689.075 / bulan**
- **Kuartil Pertama (Q1):** **Rp550.000 / bulan**
- **Kuartil Ketiga (Q3):** **Rp800.000 / bulan** (Rentang IQR = Rp250.000; batas kewajaran IQR: **Rp175.000 – Rp1.175.000**)
- **Minimum – Maksimum (Valid):** **Rp166.667 – Rp1.550.000 / bulan**

Distribusi tarif terkonsentrasi kuat pada rentang Rp550.000 sampai Rp800.000 per bulan dengan ekor kanan (*right-skewed*) pada unit kos berfasilitas eksekutif (AC, water heater, kamar mandi dalam). Oleh karena itu, **median** digunakan sebagai ukuran pemusatan utama pada visualisasi perbandingan wilayah dan fasilitas.

---

## 3. Harga Berdasarkan Kecamatan (16 Kecamatan) dan Kategori Penghuni

| Kecamatan | Jumlah Unit (`n`) | Median Tarif (`Rp/Bulan`) | Rata-rata Tarif (`Rp/Bulan`) |
|---|---:|---:|---:|
| **Balige** | 228 | Rp725.000 | Rp752.251 |
| **Laguboti** | 138 | Rp725.000 | Rp742.512 |
| **Ajibata** | 25 | Rp725.000 | Rp752.167 |
| **Porsea** | 32 | Rp612.500 | Rp637.370 |
| **Pintu Pohan Meranti** | 4 | Rp600.000 | Rp618.750 |
| **Tampahan** | 9 | Rp600.000 | Rp614.352 |
| **Parmaksian** | 9 | Rp600.000 | Rp604.630 |
| **Siantar Narumonda** | 11 | Rp600.000 | Rp584.091 |
| **Silaen** | 19 | Rp550.000 | Rp560.965 |
| **Bonatua Lunasi** | 5 | Rp550.000 | Rp550.000 |
| **Uluan** | 7 | Rp550.000 | Rp528.571 |
| **Lumban Julu** | 11 | Rp550.000 | Rp527.273 |
| **Nassau** | 7 | Rp550.000 | Rp514.286 |
| **Sigumpar** | 9 | Rp500.000 | Rp501.389 |
| **Borbor** | 26 | Rp425.000 | Rp458.333 |
| **Habinsaran** | 16 | Rp400.000 | Rp446.094 |

Perbandingan berdasarkan **Kategori Penghuni**:
- **Campur (`n = 262`):** Median **Rp700.000** (Rata-rata Rp735.283)
- **Putri (`n = 155`):** Median **Rp700.000** (Rata-rata Rp698.430)
- **Putra (`n = 139`):** Median **Rp575.000** (Rata-rata Rp591.547)

---

## 4. Distribusi Luas Kamar (`luas_kamar_m2`) dan Kategori Lantai (`kategori_lantai`)

Setelah mengevaluasi ekspresi perkalian dimensi (`4x4`, `3,5x5`, `4*3`), mengonversi input panjang 1 sisi ($1,5 \le s \le 4,0\text{ m}$ menjadi $s^2$), serta menyaring anomali luas bangunan/rumah utuh (`> 36` $\text{m}^2$):
- **Median luas kamar:** **12,0 $\text{m}^2$** (rata-rata **11,73 $\text{m}^2$**, Q1 = **9,0 $\text{m}^2$**, Q3 = **13,0 $\text{m}^2$**).

Distribusi berdasarkan **Kategori Lantai (`kategori_lantai`)**:
- **Lantai `1` (`n = 386`, termasuk normalisasi `'bawah tanah'`):** Median **Rp625.000** (Rata-rata Rp649.100)
- **Lantai `2` (`n = 168`):** Median **Rp750.000** (Rata-rata Rp781.587)
- **Lantai `3` (`n = 1`):** Median **Rp666.667**
- **Lantai `4 - 5` (`n = 1`, hasil pengelompokan lantai `> 5`):** Median **Rp600.000**

---

## 5. Hubungan Fasilitas Kamar, Kamar Mandi, dan Keamanan dengan Harga

| Kelompok | Spesifikasi Fasilitas | Jumlah Unit (`n`) | Median Tarif (`Rp/Bulan`) | Selisih Median |
|---|---|---:|---:|---:|
| **Pendingin (AC)** | Ada AC | 31 | **Rp1.208.333** | **+Rp541.666** |
| | Tanpa AC | 525 | **Rp666.667** | — |
| **Internet Wi-Fi** | Ada Wi-Fi | 391 | **Rp725.000** | **+Rp200.000** |
| | Tanpa Wi-Fi | 165 | **Rp525.000** | — |
| **Kamar Mandi** | Kamar Mandi Dalam (`dalam`) | 487 | **Rp700.000** | **+Rp200.000** |
| | Kamar Mandi Luar (`luar`) | 69 | **Rp500.000** | — |
| **Keamanan Kos** | Penjaga & CCTV | 72 | **Rp850.000** | **+Rp275.000** |
| | Penjaga/Satpam | 73 | **Rp775.000** | **+Rp200.000** |
| | CCTV (gabungan `CCTV` & `CCTV Saja`) | 179 | **Rp650.000** | **+Rp75.000** |
| | Tidak Ada | 232 | **Rp575.000** | — |

---

## 6. Hubungan Jarak Fasilitas (Satuan Meter `_m`) & Klasifikasi Jarak dengan Harga

Seluruh variabel jarak diseragamkan ke dalam satuan **meter (`m`)**, dengan nilai `0` m pada fasilitas publik eksternal (seperti 13 baris `jarak_laundry_m = 0` di Borbor) telah diimputasi menggunakan median kecamatan, lalu diuji dengan korelasi peringkat **Spearman ($\rho$)**:

| Variabel Jarak (Meter) | Koefisien Spearman ($\rho$) | Interpretasi Arah Hubungan |
|---|---:|---|
| `jarak_jalan_raya_m` | **$-0,2385$** | Korelasi negatif signifikan: semakin dekat ke jalan raya utama, harga semakin tinggi |
| `jarak_tempat_ibadah_m` | **$-0,0396$** | Negatif sangat lemah |
| `jarak_kampus_sekolah_tempatkerja_m` | **$-0,0183$** | Negatif lemah: unit lebih dekat ke kampus/kantor cenderung lebih mahal |
| `jarak_laundry_m` | **$-0,0183$** | Negatif lemah |
| `jarak_pusat_kota_m` | **$+0,1292$** | Positif lemah (dipengaruhi klaster kos mahasiswa di Sitoluama, Laguboti yang berjarak ~3 km dari pusat kecamatan) |
| `jarak_pasar_minimarket_m` | **$+0,1564$** | Positif lemah (efek klaster kos mahasiswa Sitoluama) |
| `jarak_fasilitas_kesehatan_m` | **$+0,1833$** | Positif lemah (efek klaster kos mahasiswa Sitoluama) |

---

## 7. Kualitas Data 4 Dimensi, Pembersihan Logis, Outlier IQR, dan Status Data

| Status / Indikator Kualitas | Jumlah Baris / Sel | Keterangan |
|---|---:|---|
| **Sel kosong pada Raw (`Survey_Kos_Fix.csv`)** | 50 sel | `biaya_tambahan` (37), `biaya_sewa_sudah_mencakup` (6), `status_penyewa` (4), `ada_biaya_tambahan` (2), `fasilitas_cuci_jemur` (1) |
| **Imputasi Jarak Eksternal `0` m** | 13 baris | `jarak_laundry_m = 0` diimputasi dengan median kecamatan |
| **Pembersihan Kontradiksi Fasilitas** | 8 baris | 3 baris `'Kamar Kosong'` + furnitur; 5 baris dual `'Toilet duduk, Toilet Jongkok'` |
| **Sel kosong pada Staging (`survey_clean_v1.csv`)** | **0 sel** | 100% *Completeness* setelah normalisasi & imputasi median kecamatan |
| **Exact Duplicate** | 0 baris | Tidak ditemukan duplikat identik |
| **Duplikasi Logis (`duplicate_logis`)** | 39 baris | Ditandai sebagai flag (**530 baris unik murni**) |
| **Kandidat Outlier IQR (`price_anomaly_iqr`)** | 28 baris | Di luar rentang IQR (`Rp175.000` – `Rp1.175.000`) |
| **Ditolak Validasi Domain Ketat** | 13 baris | Luas tidak logis `> 36` m² (7), harga bulanan `< Rp150.000` (6), bukan kos (1), kos tidak beroperasi (2) — beberapa baris memiliki >1 alasan |
| **Lolos Analisis Dasar (`accepted_for_analysis`)** | **556 baris** | Dimuat ke `fact_sewa_kos` di `data/tobakost_survey_warehouse.db` |
| **Siap Pemodelan Baseline (`model_ready`)** | **485 baris** | Lolos analisis, harga masih berlaku, bukan outlier IQR, bukan duplikat logis |

---

## 8. Lima Temuan Utama EDA (Ringkasan Eksekutif)

1. **Standar Tarif Pasar Kabupaten Toba:** Dari 556 unit kos valid, tarif median berada di **Rp675.000/bulan** (rata-rata Rp689.075/bulan) dengan 50% pasar utama berada di rentang **Rp550.000 – Rp800.000/bulan**.
2. **Klaster Harga Wilayah & Gender:** Tiga kecamatan pusat aktivitas (**Balige, Laguboti, dan Ajibata = median Rp725.000**) mendominasi 70% sampel dan memiliki tarif 70%–81% lebih tinggi dibanding kecamatan pinggiran (**Borbor = Rp425.000; Habinsaran = Rp400.000**). Kos Putri dan Campur (Rp700.000) secara konsisten lebih mahal Rp125.000 dibanding kos Putra (Rp575.000).
3. **Standar Luas Kamar & Premium Lantai 2:** Ukuran kamar standar setelah pembersihan dimensi 1D adalah **12 $\text{m}^2$** ($3\times 4$ m, Q1 = 9 $\text{m}^2$, Q3 = 13 $\text{m}^2$), dan kamar di **Lantai 2 (median Rp750.000)** memiliki harga Rp125.000 lebih tinggi dibanding **Lantai 1 (Rp625.000)**.
4. **Dampak Signifikan Fasilitas & Keamanan:** Fasilitas AC (+Rp541.666), Wi-Fi (+Rp200.000), Kamar Mandi Dalam (+Rp200.000), dan kelengkapan keamanan (`Tidak Ada` Rp575.000 $\rightarrow$ `CCTV` Rp650.000 $\rightarrow$ `Penjaga/Satpam` Rp775.000 $\rightarrow$ `Penjaga & CCTV` Rp850.000) menaikkan tarif secara monoton.
5. **Kedekatan dengan Jalan Raya Utama:** Dalam satuan meter, kedekatan ke jalan raya utama (`jarak_jalan_raya_m`, $\rho = -0,2385$) menjadi faktor lokasi paling menentukan bagi kenaikan tarif kos.
