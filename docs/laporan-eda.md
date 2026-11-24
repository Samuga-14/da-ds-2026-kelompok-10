# Laporan EDA Survei Kos Toba

## 1. Identitas dan Cakupan

- Dataset mentah: `data/raw/data_fix.csv`
- Dataset staging: `data/staging/survey_clean_v1.csv`
- Warehouse survei: `data/tobakost_survey_warehouse.db`
- Notebook: `notebooks/02_eda_survey.ipynb`
- Revisi laporan: 20 November 2026
- Dataset mentah: 328 baris dan 44 kolom
- Dataset staging: 328 baris dan 58 kolom kanonik/flag
- Baris lolos analisis dasar: 312
- Baris `model_ready`: 260

Harga tahunan dinormalisasi menjadi setara bulanan dengan pembagian 12.
Harga yang sudah bulanan dipertahankan. Analisis grafik menggunakan subset
`accepted_for_analysis = 1`; semua 328 baris tetap tersedia pada staging beserta
kolom flag.

## 2. Distribusi Harga Bulanan Normalisasi

Pada 312 baris lolos analisis, median harga setara bulanan adalah Rp687.500,
kuartil pertama Rp550.000, dan kuartil ketiga Rp833.333. Distribusi cenderung
condong ke kanan karena terdapat sejumlah unit bertarif tinggi. Oleh karena itu,
median lebih representatif daripada rata-rata untuk tarif umum.

## 3. Harga Berdasarkan Kecamatan dan Kategori Penghuni

Median harga berbeda antar kecamatan. Balige dan Laguboti berada pada median
yang relatif tinggi dibanding beberapa kecamatan lain, sedangkan Sigumpar menjadi
median terendah pada subset yang dianalisis. Selisih dapat dipengaruhi jumlah
sampel, karakter fasilitas, dan komposisi unit.

Perbandingan kategori penghuni bersifat deskriptif. Perbedaan kategori tidak
digunakan untuk menyimpulkan sebab-akibat karena lokasi dan fasilitas lain tidak
dikendalikan dalam grafik ini.

## 4. Luas Kamar dan Lantai

Sebaran luas kamar mayoritas berada pada rentang unit kecil hingga menengah.
Median luas perlu dibaca bersama grafik distribusi agar tidak menyembunyikan
kemiringan atau nilai ekstrem.

Sebanyak 227 dari 312 baris pada subset analisis berada di lantai 1 dan median
tarifnya Rp650.000. Lantai 2 mempunyai 82 baris dengan median Rp800.000.
Lantai 3 dan lantai 9 hanya masing-masing berisi satu baris sehingga tidak cukup
untuk generalisasi. Nilai lantai 9 perlu ditinjau sebagai kandidat anomali data,
bukan langsung dibuang.

## 5. Hubungan Fasilitas dengan Harga

Fasilitas AC, Wi-Fi, dan tipe kamar mandi dibandingkan menggunakan median tarif.
Nilai median dipilih untuk mengurangi dampak nilai ekstrem. Karena analisis belum
melakukan pengendalian lokasi, luas kamar, dan lantai, hasilnya hanya menunjukkan
hubungan deskriptif.

## 6. Hubungan Jarak Fasilitas dengan Harga

Setiap kolom jarak dihitung korelasinya dengan tarif menggunakan korelasi Spearman.
Metode ini dipilih agar tidak mengasumsikan hubungan linear. Koefisien mendekati nol
menunjukkan jarak tidak memiliki hubungan monoton yang kuat pada sampel. Koefisien
negatif dapat berarti unit yang lebih dekat cenderung mempunyai tarif lebih tinggi,
tetapi perlu ditinjau bersama lokasi dan fasilitas.

## 7. Missing, Outlier, dan Status Data

Missing utama pada staging adalah:

| Kolom | Jumlah kosong |
|---|---:|
| `tahun_mulai_menyewa` | 328 |
| `biaya_sewa_sudah_mencakup` | 6 |
| `ada_biaya_tambahan` | 2 |
| `jumlah_lantai` | 1 |
| `jarak_kampus_sekolah_tempatkerja_m` | 1 |
| `fasilitas_cuci_jemur` | 1 |

Missing tidak diimputasi secara sembarang. Kolom sumber `tahun_mulai_menyewa`
kosong pada seluruh staging karena informasi tersebut tidak tersedia pada ekspor saat ini.

Metode IQR menemukan 25 kandidat outlier dari 328 baris. Kandidat outlier ditandai,
bukan dihapus. Pengujian dan pembenaran harus memeriksa periode sewa, luas, lantai,
lokasi, dan fasilitas sebelum baris dinyatakan salah.

Status data pada staging:

| Status | Jumlah |
|---|---:|
| Exact duplicate | 0 |
| Baris terlibat duplikasi logis | 30 |
| Kandidat outlier IQR | 25 |
| Lolos analisis dasar | 312 |
| `model_ready` | 260 |

## 8. Kesimpulan

1. Gunakan `harga_bulanan_norm` sebagai target atau metrik tarif lintas periode.
2. Gunakan median untuk ringkasan lokasi dan fasilitas yang kuat terhadap outlier.
3. Pertahankan semua flag audit pada staging; jangan menghapus baris mentah atau staging.
4. Tinjau lantai 9 dan kandidat IQR sebelum pemakaian model lanjutan.
5. Gunakan baris `model_ready = 1` untuk baseline model konservatif.

