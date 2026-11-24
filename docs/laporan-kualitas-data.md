# Laporan Kualitas Data Survei Kos Toba

## Ringkasan

Dataset mentah utama yang dianalisis adalah `data/raw/Survey_Kos.csv` dengan **928 baris** dan
**35 kolom** (telah memenuhi syarat minimum $\ge 500$ baris data primer). File raw tidak diubah.
Pipeline preprocessing (`etl/normalize_survey.py`) menghasilkan dataset staging bersih pada
`data/staging/survey_clean_v1.csv` (928 baris, 74 kolom fitur & metadata kualitas) serta laporan
terstruktur pada `data/quality/survey_quality_v1.json`.

## Temuan Utama

| Pemeriksaan | Hasil |
|---|---:|
| Jumlah baris raw (`Survey_Kos.csv`) | 928 |
| Jumlah baris staging (`survey_clean_v1.csv`) | 928 |
| Exact duplicate | 0 |
| Duplikasi logis (`duplicate_logis`) | 42 baris terlibat |
| Kandidat outlier IQR (`price_anomaly_iqr`) | 42 |
| Lolos analisis dasar (`accepted_for_analysis`) | 923 |
| Siap pemodelan baseline (`model_ready`) | 833 |
| Baris ditolak atau kos tidak aktif | 5 |

## Pengukuran 4 Dimensi Kualitas Data (Sebelum vs Sesudah Preprocessing)

| Dimensi Kualitas | Sebelum Preprocessing (Raw) | Sesudah Preprocessing (Staging) | Tindakan Normalisasi |
|---|---|---|---|
| **1. Completeness** | 37 sel kosong (`status_penyewa`, `biaya_tambahan`, `fasilitas_cuci_jemur`, `biaya_sewa_sudah_mencakup`, 1 jarak kampus tanpa angka) | **0 sel kosong** (100% terisi) | Imputasi jarak kampus kosong dengan median kecamatan; kategori kosong dipetakan ke nilai default kanonik (`Tidak Disebutkan`, `Tidak`, `0`) |
| **2. Validity** | 42 baris luas kamar ditulis ekspresi perkalian (`4x4`, `3,5x5`), 1 baris `2000` m², lantai `bawah tanah` & lantai `9`, harga singkat (`7`, `250`, `700`, `900`, `60000`), jarak `300010` m | **924 baris** memiliki harga & luas kamar valid; **926 baris** kos aktif; **923 baris** lolos ke warehouse (`fact_sewa_kos`) | Evaluasi perkalian dimensi $P \times L$; koreksi typo `2000` -> `200` m² & jarak `300010` -> `3000` m; konversi harga singkat ke nominal Rupiah penuh; lantai `bawah tanah` -> `1` dan `> 5` -> `4` (`kategori_lantai`: `'4 - 5'`) |
| **3. Consistency** | Satuan jarak campuran (`km` vs `m`), harga berformat titik (`700.000` vs `700000`), biaya tambahan `'100rb'`, kategori ganda (`CCTV Saja` vs `CCTV`, `Dalam` vs `Kamar mandi dalam`, `Mobil` vs `Mobil & Motor`) | **100% konsisten** dalam satuan meter (`_m` + klasifikasi jarak 4 tingkat), Rupiah bulat tanpa titik, dan kategori standar | Konversi seluruh jarak ke meter (`_m`) beserta `klasifikasi_jarak_*`; penyeragaman `CCTV Saja` -> `CCTV`, `Dalam` -> `dalam`, `Mobil` -> `Mobil & Motor`, `Ada Batas Jam Tertentu` -> `Ada Batas Jam Malam` |
| **4. Uniqueness** | 0 exact duplicate; variasi ejaan nama desa/kelurahan (`Pintubosi` vs `Pintu Bosi`, `Balige 1` vs `Balige I`) | **0 exact duplicate**; **42 baris** ditandai sebagai `duplicate_logis` (886 baris unik murni) | Standarisasi nama desa/kelurahan sebelum pengecekan duplikasi logis; baris duplikasi logis diberi flag tanpa dihapus dari staging |

## Aturan Preprocessing yang Diterapkan

1. **Luas Kamar (`luas_kamar_m2`):**
   - Ekspresi dimensi seperti `4×4`, `3,5x5`, `3x6 m2` dihitung hasil perkaliannya ($16.0$, $17.5$, $18.0\text{ m}^2$).
   - Angka ekstrem karena kelebihan ketik nol seperti `2000` dikoreksi menjadi `200` $\text{m}^2$.
2. **Jarak dalam Satuan Meter (`jarak_*_m`) & Klasifikasi Jarak (`klasifikasi_jarak_*`):**
   - Seluruh 7 variabel jarak diseragamkan ke dalam satuan **meter (`m`)**.
   - Input dengan satuan `km` (mis. `1,5 km`, `2.8 Km`, `Sekolah 5 km`) dikalikan `1000`.
   - Input angka tunggal `1`–`5` (yang mengindikasikan kilometer) dikalikan `1000`, serta typo `300010` dikoreksi menjadi `3000` m.
   - Setiap kolom jarak dilengkapi kolom klasifikasi:
     - `Sangat Dekat (<= 500 m)`
     - `Dekat (501 - 1000 m)`
     - `Sedang (1001 - 3000 m)`
     - `Jauh (> 3000 m)`
3. **Posisi Lantai Kamar (`jumlah_lantai` & `kategori_lantai`):**
   - Jawaban `'bawah tanah'` dipetakan menjadi lantai `1`.
   - Jawaban lantai di atas 5 (seperti `'9'`) dipetakan ke nilai numerik `4` dengan label `kategori_lantai = '4 - 5'`.
4. **Nominal Harga Sewa (`harga_sewa` & `harga_bulanan_norm`):**
   - Seluruh format titik pemisah ribuan (`400.000`, `700.000`, `2.000.000`) diseragamkan menjadi integer murni (`400000`, `700000`, `2000000`).
   - Penulisan singkat responden diskalakan secara otomatis: angka satuan/puluhan `< 100` (seperti `7` Per Tahun -> `7000000`, atau `7` Per Bulan -> `700000`), ratusan `< 2000` (seperti `250`, `500`, `700`, `900` -> dikali `1000`), dan puluhan ribu yang kurang satu nol (`10000`, `60000` -> dikali `10`).
   - Harga tahunan dikonversi ke ekuivalen bulanan (`harga_sewa / 12`).
   - Metode IQR pada data valid menghasilkan batas kewajaran harga bulanan:
     - **Batas bawah:** `Rp229.687,50`
     - **Batas atas:** `Rp1.142.187,50`
5. **Standarisasi Kategori:**
   - **Keamanan Kos (`keamanan_kos`):** `'CCTV Saja'` dan `'CCTV'` disatukan menjadi **`'CCTV'`** (kategori akhir: `'CCTV'`, `'Penjaga/Satpam'`, `'Penjaga & CCTV'`, `'Tidak Ada'`).
   - **Tipe Kamar Mandi (`tipe_kamar_mandi`):** `'dalam'` dan `'luar'`.
   - **Lahan Parkir (`lahan_parkir`):** `'Mobil & Motor'`, `'Motor Saja'`, dan `'Tidak Ada'`.
   - **Aturan Jam Malam (`aturan_jam_malam`):** `'Bebas 24 Jam'` dan `'Ada Batas Jam Malam'`.

## Verifikasi Teknis

```text
python etl/normalize_survey.py
raw_rows=928, staging_rows=928, staging_columns=74, exact_duplicates=0
logical_duplicate_rows=42, price_anomaly_iqr=42
accepted_for_analysis=923, model_ready=833

python etl/run_survey_star_schema.py
Fact rows: 923
Model-ready rows: 833

python -m unittest tests/test_normalize_survey.py -v
Ran 8 tests in 0.999s - OK
```
