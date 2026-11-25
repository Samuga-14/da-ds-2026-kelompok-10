# Laporan EDA Survei Kos Toba (928 Baris)

## 1. Identitas dan Cakupan Dataset

- **Dataset mentah utama:** `data/raw/Survey_Kos.csv` (**928 baris**, **35 kolom**)
- **Dataset staging bersih:** `data/staging/survey_clean_v1.csv` (**928 baris**, **74 kolom** kanonik, klasifikasi jarak, & flag kualitas, **0 sel kosong**)
- **Warehouse survei skema bintang:** `data/tobakost_survey_warehouse.db` (**923 baris** pada `fact_sewa_kos`)
- **Subset siap pemodelan (`model_ready = 1`):** **833 baris**
- **Notebook eksperimen:** `notebooks/01_profiling_survey.ipynb` dan `notebooks/02_eda_survey.ipynb`
- **Revisi laporan:** 25 November 2026

Harga sewa tahunan dinormalisasi menjadi setara bulanan (`harga_bulanan_norm = harga_sewa / 12`), sedangkan harga bulanan dipertahankan. Seluruh analisis eksploratif menggunakan subset valid `accepted_for_analysis = 1` (**923 baris**), sementara seluruh 928 baris tetap tersimpan utuh beserta kolom flag audit di staging.

---

## 2. Distribusi Harga Bulanan Normalisasi (`harga_bulanan_norm`)

Pada **923 baris** unit kos yang lolos validasi dasar:
- **Median:** **Rp700.000 / bulan**
- **Rata-rata (Mean):** **Rp693.929 / bulan**
- **Kuartil Pertama (Q1):** **Rp575.000 / bulan**
- **Kuartil Ketiga (Q3):** **Rp800.000 / bulan** (Rentang IQR = Rp225.000)
- **Minimum – Maksimum (Valid):** **Rp100.000 – Rp1.550.000 / bulan**

Distribusi tarif terkonsentrasi kuat pada rentang Rp575.000 sampai Rp800.000 per bulan dengan ekor kanan (*right-skewed*) pada unit kos berfasilitas eksekutif (AC, water heater, kamar mandi dalam). Oleh karena itu, **median** digunakan sebagai ukuran pemusatan utama pada visualisasi perbandingan wilayah dan fasilitas.

---

## 3. Harga Berdasarkan Kecamatan (16 Kecamatan) dan Kategori Penghuni

| Kecamatan | Jumlah Unit (`n`) | Median Tarif (`Rp/Bulan`) | Rata-rata Tarif (`Rp/Bulan`) |
|---|---:|---:|---:|
| **Laguboti** | 254 | Rp725.000 | Rp738.533 |
| **Porsea** | 104 | Rp725.000 | Rp705.769 |
| **Ajibata** | 56 | Rp725.000 | Rp750.967 |
| **Balige** | 355 | Rp700.000 | Rp721.446 |
| **Parmaksian** | 16 | Rp612.500 | Rp610.417 |
| **Tampahan** | 11 | Rp604.167 | Rp607.576 |
| **Siantar Narumonda** | 14 | Rp600.000 | Rp601.786 |
| **Uluan** | 8 | Rp562.500 | Rp571.875 |
| **Silaen** | 23 | Rp550.000 | Rp555.072 |
| **Lumban Julu** | 14 | Rp550.000 | Rp537.202 |
| **Nassau** | 8 | Rp500.000 | Rp476.563 |
| **Sigumpar** | 11 | Rp475.000 | Rp476.136 |
| **Borbor** | 14 | Rp462.500 | Rp470.833 |
| **Bonatua Lunasi** | 8 | Rp450.000 | Rp458.854 |
| **Habinsaran** | 19 | Rp425.000 | Rp457.237 |
| **Pintu Pohan Meranti** | 8 | Rp352.084 | Rp450.521 |

Perbandingan berdasarkan **Kategori Penghuni**:
- **Campur (`n = 403`):** Median **Rp725.000** (Rata-rata Rp740.908)
- **Putri (`n = 264`):** Median **Rp725.000** (Rata-rata Rp717.781)
- **Putra (`n = 256`):** Median **Rp575.000** (Rata-rata Rp595.378)

---

## 4. Distribusi Luas Kamar (`luas_kamar_m2`) dan Kategori Lantai (`kategori_lantai`)

Setelah menormalisasi 42 baris yang ditulis dalam format perkalian dimensi (`4x4`, `3,5x5`, `3x6 m2`) serta mengoreksi typo `2000` $\rightarrow$ `200` $\text{m}^2$:
- **Median luas kamar:** **12,0 $\text{m}^2$** (rata-rata **12,68 $\text{m}^2$**, Q1 = **10,0 $\text{m}^2$**, Q3 = **13,0 $\text{m}^2$**).

Distribusi berdasarkan **Kategori Lantai (`kategori_lantai`)**:
- **Lantai `1` (`n = 630`, termasuk normalisasi `'bawah tanah'`):** Median **Rp650.000** (Rata-rata Rp663.000)
- **Lantai `2` (`n = 290`):** Median **Rp750.000** (Rata-rata Rp763.069)
- **Lantai `3` (`n = 2`):** Median **Rp458.334**
- **Lantai `4 - 5` (`n = 1`, hasil pengelompokan lantai `> 5`):** Median **Rp600.000**

---

## 5. Hubungan Fasilitas Kamar, Kamar Mandi, dan Keamanan dengan Harga

| Kelompok | Spesifikasi Fasilitas | Jumlah Unit (`n`) | Median Tarif (`Rp/Bulan`) | Selisih Median |
|---|---|---:|---:|---:|
| **Pendingin (AC)** | Ada AC | 42 | **Rp1.200.000** | **+Rp525.000** |
| | Tanpa AC | 881 | **Rp675.000** | — |
| **Internet Wi-Fi** | Ada Wi-Fi | 667 | **Rp750.000** | **+Rp200.000** |
| | Tanpa Wi-Fi | 256 | **Rp550.000** | — |
| **Kamar Mandi** | Kamar Mandi Dalam (`dalam`) | 863 | **Rp700.000** | **+Rp200.000** |
| | Kamar Mandi Luar (`luar`) | 60 | **Rp500.000** | — |
| **Keamanan Kos** | Penjaga & CCTV | 73 | **Rp850.000** | **+Rp225.000** |
| | Penjaga/Satpam | 215 | **Rp750.000** | **+Rp125.000** |
| | CCTV (gabungan `CCTV` & `CCTV Saja`) | 176 | **Rp650.000** | **+Rp25.000** |
| | Tidak Ada | 459 | **Rp625.000** | — |

---

## 6. Hubungan Jarak Fasilitas (Satuan Meter `_m`) & Klasifikasi Jarak dengan Harga

Seluruh variabel jarak diseragamkan ke dalam satuan **meter (`m`)** dan diuji menggunakan korelasi peringkat **Spearman ($\rho$)**:

| Variabel Jarak (Meter) | Koefisien Spearman ($\rho$) | Interpretasi Arah Hubungan |
|---|---:|---|
| `jarak_jalan_raya_m` | **$-0,3975$** | Korelasi negatif sedang-kuat: semakin dekat ke jalan raya utama, harga semakin tinggi |
| `jarak_kampus_sekolah_tempatkerja_m` | **$-0,0652$** | Korelasi negatif lemah: unit lebih dekat ke kampus/kantor cenderung lebih mahal |
| `jarak_laundry_m` | **$-0,0367$** | Mendekati nol |
| `jarak_tempat_ibadah_m` | **$-0,0360$** | Mendekati nol |
| `jarak_pusat_kota_m` | **$+0,0856$** | Positif lemah (dipengaruhi konsentrasi kos mahasiswa di Sitoluama, Laguboti yang berjarak ~3 km dari pusat kecamatan) |
| `jarak_pasar_minimarket_m` | **$+0,1110$** | Positif lemah (efek klaster kos mahasiswa Sitoluama) |
| `jarak_fasilitas_kesehatan_m` | **$+0,1331$** | Positif lemah (efek klaster kos mahasiswa Sitoluama) |

Berdasarkan **`klasifikasi_jarak_kampus_sekolah_tempatkerja`**:
- **`Sangat Dekat (<= 500 m)` (`n = 482`):** Median **Rp700.000** (Rata-rata Rp705.088)
- **`Dekat (501 - 1000 m)` (`n = 338`):** Median **Rp675.000** (Rata-rata Rp684.702)
- **`Sedang (1001 - 3000 m)` (`n = 99`):** Median **Rp675.000** (Rata-rata Rp676.330)
- **`Jauh (> 3000 m)` (`n = 4`):** Median **Rp570.834** (Rata-rata Rp564.584)

---

## 7. Kualitas Data 4 Dimensi, Missing Value, Outlier IQR, dan Status Data

| Status / Indikator Kualitas | Jumlah Baris / Sel | Keterangan |
|---|---:|---|
| **Sel kosong pada Raw (`Survey_Kos.csv`)** | 37 sel | `biaya_tambahan` (24), `biaya_sewa_sudah_mencakup` (6), `status_penyewa` (4), `ada_biaya_tambahan` (2), `fasilitas_cuci_jemur` (1) |
| **Sel kosong pada Staging (`survey_clean_v1.csv`)** | **0 sel** | 100% *Completeness* setelah normalisasi & imputasi median kecamatan pada 1 jarak kampus |
| **Exact Duplicate** | 0 baris | Tidak ditemukan duplikat identik |
| **Duplikasi Logis (`duplicate_logis`)** | 42 baris | Ditandai sebagai flag (886 baris unik murni) |
| **Kandidat Outlier IQR (`price_anomaly_iqr`)** | 42 baris | Di luar rentang IQR (`Rp229.687,50` – `Rp1.142.187,50`) |
| **Lolos Analisis Dasar (`accepted_for_analysis`)** | **923 baris** | Dimuat ke `fact_sewa_kos` di `data/tobakost_survey_warehouse.db` |
| **Siap Pemodelan Baseline (`model_ready`)** | **833 baris** | Lolos analisis, harga masih berlaku, bukan outlier IQR, bukan duplikat logis |

---

## 8. Lima Temuan Utama EDA (Ringkasan Eksekutif)

1. **Standar Tarif Pasar Kabupaten Toba:** Dari 923 unit kos valid, tarif median berada di **Rp700.000/bulan** dengan 50% pasar utama berada di rentang sempit **Rp575.000 – Rp800.000/bulan**.
2. **Klaster Harga Wilayah & Gender:** Empat kecamatan pusat aktivitas (**Laguboti, Porsea, Ajibata = Rp725.000; Balige = Rp700.000**) mendominasi 83% sampel dan memiliki tarif hampir dua kali lipat kecamatan pinggiran (**Pintu Pohan Meranti = Rp352.084**). Kos Putri dan Campur (Rp725.000) secara konsisten lebih mahal Rp150.000 dibanding kos Putra (Rp575.000).
3. **Standar Luas Kamar & Premium Lantai 2:** Ukuran kamar standar adalah **12 $\text{m}^2$** ($3\times 4$ m), dan kamar di **Lantai 2 (median Rp750.000)** memiliki harga Rp100.000 lebih tinggi dibanding **Lantai 1 (Rp650.000)**.
4. **Dampak Signifikan Fasilitas & Keamanan:** Fasilitas AC (+Rp525.000), Wi-Fi (+Rp200.000), Kamar Mandi Dalam (+Rp200.000), dan kelengkapan keamanan (`Tidak Ada` Rp625.000 $\rightarrow$ `CCTV` Rp650.000 $\rightarrow$ `Penjaga/Satpam` Rp750.000 $\rightarrow$ `Penjaga & CCTV` Rp850.000) menaikkan tarif secara monoton.
5. **Kedekatan dengan Jalan Raya Utama & Kampus/Kantor:** Dalam satuan meter, kedekatan ke jalan raya utama (`jarak_jalan_raya_m`, $\rho = -0,3975$) dan radius `<= 500 m` dari kampus/kantor/sekolah (median Rp700.000) menjadi faktor lokasi paling menentukan bagi tarif kos.
