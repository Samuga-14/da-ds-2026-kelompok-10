# Laporan Kualitas Data Survei Kos Toba (`Survey_Kos_Fix.csv`)

## Ringkasan

Dataset mentah utama yang dianalisis adalah `data/raw/Survey_Kos_Fix.csv` dengan **569 baris** dan
**35 kolom** (telah memenuhi syarat minimum $\ge 500$ baris data primer). File raw tidak diubah.
Pipeline preprocessing & pembersihan logis ketat (`etl/normalize_survey.py`) menghasilkan dataset
staging bersih pada `data/staging/survey_clean_v1.csv` (**569 baris**, **74 kolom** fitur & metadata
kualitas) serta laporan audit terstruktur pada `data/quality/survey_quality_v1.json`.

## Temuan Utama

| Pemeriksaan | Hasil |
|---|---:|
| Jumlah baris raw (`Survey_Kos_Fix.csv`) | 569 |
| Jumlah baris staging (`survey_clean_v1.csv`) | 569 |
| Exact duplicate | 0 |
| Duplikasi logis (`duplicate_logis`) | 39 baris terlibat (530 baris unik murni) |
| Kandidat outlier IQR (`price_anomaly_iqr`) | 28 |
| Lolos analisis dasar & validasi logis (`accepted_for_analysis`) | **556** |
| Siap pemodelan baseline (`model_ready`) | **485** |
| Baris ditolak oleh validasi logis ketat (`rejection_reason != ""`) | 13 |

## Pengukuran 4 Dimensi Kualitas Data (Sebelum vs Sesudah Preprocessing Ketat)

| Dimensi Kualitas | Sebelum Preprocessing (Raw) | Sesudah Preprocessing (Staging) | Tindakan Normalisasi & Cleaning Logis |
|---|---|---|---|
| **1. Completeness** | **50 sel kosong** (`biaya_tambahan` 37, `biaya_sewa_sudah_mencakup` 6, `status_penyewa` 4, `ada_biaya_tambahan` 2, `fasilitas_cuci_jemur` 1) + **13 baris** `jarak_laundry_m = 0` m + **1 baris** jarak kampus tanpa angka (`'Kantor'`) | **0 sel kosong** (100% terisi) & **0 jarak fasilitas eksternal bernilai 0 m** | Imputasi jarak kosong dan jarak fasilitas eksternal `0` m dengan median kecamatan yang sama; kategori kosong dipetakan ke nilai default kanonik (`Tidak Disebutkan`, `Tidak`, `0`) |
| **2. Validity** | Ekspresi dimensi (`4x4`, `3,5x5`, `4*3`), input panjang 1 sisi (`2`, `3`, `3 m2`, `3 meter`, `4 m`), luas rumah utuh (`42`, `60`, `112`, `200`, `224`, `240`, `2000` m²), lantai `bawah tanah` & lantai `9`, harga singkat (`7`, `250`, `700`, `900`, `10000`, `60000`, `70000`), entitas non-kos (`'Bukan kos tapi rumah keluarga'`) | **557 baris** valid secara numerik & domain; **567 baris** kos aktif; **556 baris** lolos ke warehouse (`fact_sewa_kos`) | Evaluasi perkalian $P \times L$; konversi input 1 sisi ($1,5 \le s \le 4,0\text{ m}$) menjadi luas persegi $s^2$; penolakan luas tidak logis (`< 4` atau `> 36` m² — 7 baris), harga bulanan tidak logis (`< Rp150.000` atau `> Rp5.000.000` — 6 baris), dan entitas non-kos (1 baris) |
| **3. Consistency** | Satuan jarak campuran (`km` vs `m`), harga berformat titik (`750.000`), biaya tambahan `'100rb'` atau `'Tidak'` tetapi nominal `8150000`/`50000`, fasilitas kamar kontradiktif (`'Kamar Kosong'` + `'Kasur, Lemari, Ventilasi'`), kloset ganda (`'Toilet duduk, Toilet Jongkok'`), kategori ganda (`CCTV Saja` vs `CCTV`) | **100% konsisten** dalam satuan meter (`_m` + klasifikasi jarak 4 tingkat), Rupiah bulat, dan konsistensi silang antar-kolom | Pembersihan kontradiksi `'Kamar Kosong'` (3 baris) & dual kloset duduk+jongkok (5 baris); rekonsiliasi `ada_biaya_tambahan` vs `biaya_tambahan_rp`; penyeragaman `CCTV Saja` -> `CCTV`, `Dalam` -> `dalam`, `Mobil` -> `Mobil & Motor`, serta perapian spasi ganda nama kos (`'Kos  birong'` -> `'Kos Birong'`) |
| **4. Uniqueness** | 0 exact duplicate; variasi ejaan nama kos & desa/kelurahan (`Pintubosi` vs `Pintu Bosi`, `Balige 1` vs `Balige I`) | **0 exact duplicate**; **39 baris** ditandai sebagai `duplicate_logis` (**530 baris unik murni**) | Standarisasi nama kos dan desa/kelurahan sebelum pengecekan duplikasi logis; baris duplikasi logis diberi flag tanpa dihapus dari staging |

## Aturan Preprocessing & Pembersihan Logis Ketat yang Diterapkan

1. **Pembersihan Entitas & Nama Kos (`nama_kost`):**
   - Menghapus spasi ganda/berlebih (`'Kos  birong'` $\rightarrow$ `'Kos Birong'`, `'Kos Horatio  '` $\rightarrow$ `'Kos Horatio'`) dan menyeragamkan huruf kapital dengan mempertahankan akronim (`LH`, `GKPI`, `HKBP`, `SAS`, `IT`).
   - Memetakan placeholder (`'-'`, `'Tidak ada'`, `'Tidak ada nama'`) menjadi `'Kos Tanpa Nama'`.
   - Menolak entitas yang secara eksplisit menyatakan bukan kos (`'Bukan kos tapi rumah keluarga'`).
2. **Luas Kamar (`luas_kamar_m2`):**
   - Ekspresi perkalian dimensi dengan `x`, `X`, `×`, maupun `*` (`4×4`, `4*3`, `3,5x5`, `3x6 m2`) dihitung hasil perkaliannya ($16.0$, $12.0$, $17.5$, $18.0\text{ m}^2$).
   - Input angka tunggal pendek $1,5 \le s \le 4,0$ (`'2'`, `'3'`, `'3 m2'`, `'3 meter'`, `'3.5'`, `'4'`, `'4 m'`) yang merupakan panjang 1 sisi kamar dikonversi menjadi luas persegi $s \times s$ ($4.0$, $9.0$, $12.25$, $16.0\text{ m}^2$).
   - Angka ekstrem karena kelebihan ketik nol seperti `2000` dikoreksi menjadi `200` $\text{m}^2$.
   - **Batas Domain Ketat:** Luas kamar kos tunggal wajib berada pada rentang **$4,0\text{ m}^2 \le \text{luas\_kamar\_m2} \le 36,0\text{ m}^2$**. Luas bangunan/rumah utuh (`42`, `60`, `112`, `200`, `224`, `240` $\text{m}^2$) ditolak dari `accepted_for_analysis` dengan alasan `"luas kamar tidak logis (< 4 m2 atau > 36 m2)"`.
3. **Jarak dalam Satuan Meter (`jarak_*_m`) & Imputasi Logis Jarak `0` m:**
   - Seluruh 7 variabel jarak diseragamkan ke dalam satuan **meter (`m`)** beserta 7 kolom `klasifikasi_jarak_*` (`Sangat Dekat (<= 500 m)`, `Dekat (501 - 1000 m)`, `Sedang (1001 - 3000 m)`, `Jauh (> 3000 m)`).
   - Input dengan satuan `km` (`1,5 km`, `2.8 Km`, `Sekolah 5 km`) dan angka tunggal `1`–`5` dikalikan `1000`; typo `300010` dikoreksi menjadi `3000` m.
   - **Aturan Logis Jarak 0 Meter:** Nilai `0` m hanya valid untuk `jarak_jalan_raya_m` (kos tepat di pinggir jalan raya utama). Untuk fasilitas publik eksternal (`jarak_laundry_m` yang memiliki 13 baris bernilai `0` di Kec. Borbor, pasar, puskesmas, tempat ibadah, pusat kota), nilai `0` m dianggap placeholder kosong dan diimputasi dengan **median kecamatan setempat**.
4. **Posisi Lantai Kamar (`jumlah_lantai` & `kategori_lantai`):**
   - Jawaban `'bawah tanah'` dipetakan menjadi lantai `1`.
   - Jawaban lantai di atas 5 (seperti `'9'`) dipetakan ke nilai numerik `4` dengan label `kategori_lantai = '4 - 5'`.
5. **Nominal Harga Sewa (`harga_sewa` & `harga_bulanan_norm`):**
   - Format titik pemisah ribuan (`400.000`, `700.000`, `750.000`, `2.000.000`) diseragamkan menjadi integer murni.
   - Penulisan singkat diskalakan otomatis: `< 100` (`7` Per Tahun $\rightarrow$ `7000000`), `< 2000` (`250`, `500`, `700`, `900` $\rightarrow$ dikali `1000`), dan `< 100000` yang kurang satu nol (`10000`, `60000`, `70000` $\rightarrow$ dikali `10`).
   - Harga tahunan dikonversi ke ekuivalen bulanan (`harga_sewa / 12`).
   - **Batas Domain Ketat:** Tarif bulanan kos wajib berada pada rentang **$\text{Rp}150.000 \le \text{harga\_bulanan\_norm} \le \text{Rp}5.000.000$**. Baris yang menghasilkan harga bulanan tidak logis di bawah Rp150.000/bulan (akibat salah pilih periode `Per Tahun` untuk harga bulanan, mis. Rp350.000/tahun = Rp29.167/bulan) ditolak secara otomatis.
   - Metode IQR pada data valid menghasilkan batas kewajaran harga bulanan:
     - **Batas bawah:** `Rp175.000,00`
     - **Batas atas:** `Rp1.175.000,00`
6. **Konsistensi Logis Fasilitas & Biaya Tambahan:**
   - **Fasilitas Kamar (`fasilitas_kamar_detail`):** Menghapus label kontradiktif `'Kamar Kosong (...)'` pada 3 baris yang sebenarnya memilih fasilitas kamar (`Kasur`, `Lemari`, `Ventilasi Jendela`, `Gorden`).
   - **Kelengkapan Kamar Mandi (`kloset_duduk` vs `kloset_jongkok`):** Menyelesaikan kontradiksi 5 baris yang mencentang `'Toilet duduk, Toilet Jongkok'` sekaligus berdasarkan tipe kamar mandi (`km_dalam = 1` $\rightarrow$ `kloset_duduk`, `km_dalam = 0` $\rightarrow$ `kloset_jongkok`).
   - **Biaya Tambahan (`ada_biaya_tambahan` & `biaya_tambahan_rp`):** Memaksa `biaya_tambahan_rp = 0` bila `ada_biaya_tambahan == 'Tidak'` (mengoreksi baris dengan input `8150000` dan `50000`), serta menyelaraskan `ada_biaya_tambahan = 'Tidak'` apabila responden menjawab `'Ada'` tetapi mengosongkan nominal biaya tambahan.

## Verifikasi Teknis

```text
python etl/normalize_survey.py
raw_rows=569, staging_rows=569, staging_columns=74, exact_duplicates=0
logical_duplicate_rows=39, price_anomaly_iqr=28
accepted_for_analysis=556, model_ready=485

python etl/run_survey_star_schema.py
Fact rows: 556
Model-ready rows: 485

python -m unittest discover -s tests -v
Ran 22 tests in 1.518s - OK
```
