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

Analisis Issue #26 membandingkan tarif setara bulanan berdasarkan AC, Wi-Fi,
tipe kamar mandi, keamanan kos, dan lahan parkir pada subset 312 baris
`accepted_for_analysis = 1`. Ringkasan menggunakan median sebagai ukuran pusat
utama dan rata-rata sebagai pelengkap. Kandidat outlier dihitung dengan aturan IQR
per kelompok, tanpa menghapus baris.

| Fasilitas | Kelompok | Ukuran | Median Rp/bulan | Rata-rata Rp/bulan | Outlier IQR |
|---|---|---:|---:|---:|---:|
| AC | Ada AC | 312 | 687.500 | 721.958 | 13 |
| Wi-Fi | Ada Wi-Fi | 242 | 750.000 | 770.200 | 14 |
| Wi-Fi | Tanpa Wi-Fi | 70 | 550.000 | 555.179 | 2 |
| Kamar mandi | Dalam | 256 | 725.000 | 770.785 | 14 |
| Kamar mandi | Luar | 56 | 500.000 | 498.750 | 6 |
| Keamanan | Penjaga & CCTV | 70 | 850.000 | 943.869 | 1 |
| Keamanan | CCTV saja | 170 | 650.000 | 694.000 | 10 |
| Keamanan | Tidak ada | 72 | 550.000 | 572.222 | 1 |
| Parkir | Mobil & Motor | 143 | 825.000 | 866.568 | 10 |
| Parkir | Motor saja | 131 | 600.000 | 624.129 | 5 |
| Parkir | Tidak ada | 38 | 500.000 | 515.022 | 2 |

Pada seluruh 328 baris staging, kolom `ac` bernilai `1` sehingga tidak tersedia
kelompok pembanding tanpa AC. Karena itu, pengaruh AC tidak dapat dihitung dari data ini.

Unit dengan Wi-Fi memiliki median Rp200.000 lebih tinggi daripada unit tanpa Wi-Fi;
kamar mandi dalam median Rp225.000 lebih tinggi daripada kamar mandi luar.
Untuk keamanan, median Penjaga & CCTV Rp200.000 di atas CCTV saja dan Rp300.000
di atas tanpa keamanan. Untuk parkir, median Mobil & Motor Rp225.000 di atas
Motor saja dan Rp325.000 di atas tanpa parkir. Perbedaan ini deskriptif:
lokasi, luas kamar, lantai, tipe penghuni, dan kombinasi fasilitas belum
dikendalikan. Ukuran kelompok juga tidak seimbang. Temuan tidak membuktikan
sebab-akibat atau nilai tambahan tarif yang dapat dipastikan.

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

