# Data Dictionary

Dataset utama: `data/raw/Survey_Kos_Fix.csv` (**569 baris, 35 kolom**)

File raw survey tidak diubah oleh pipeline. Output staging dibuat oleh
`python etl/normalize_survey.py` di `data/staging/survey_clean_v1.csv` (569 baris, 74 kolom).
Laporan kualitas data 4 dimensi (*Completeness, Validity, Consistency, Uniqueness*) beserta
audit tindakan pembersihan logis tersedia di `data/quality/survey_quality_v1.json`.

## Variabel Utama

| Kolom staging | Definisi | Tipe | Satuan / Format | Catatan Preprocessing & Validasi Logis |
|---|---|---|---|---|
| `timestamp_survei` | Waktu pengisian kuesioner Google Form | string | `DD/MM/YYYY HH:MM:SS` | Dipertahankan untuk pelacakan audit |
| `nama_kost` | Nama kos yang ditinggali responden | string | Title Case | Spasi ganda dirapikan (`Kos  birong` -> `Kos Birong`); `-`/`Tidak ada`/`Tidak ada nama` -> `Kos Tanpa Nama`; entitas `Bukan kos...` ditolak |
| `kecamatan` | Kecamatan lokasi kos di Kabupaten Toba | kategori | Title Case | 16 kecamatan di Kabupaten Toba |
| `desa_kelurahan` | Desa atau kelurahan lokasi kos | kategori | Title Case | Sinonim & variasi ejaan disatukan (`Pintubosi` -> `Pintu Bosi`, `Balige 1` -> `Balige I`, dll.) |
| `kategori_penghuni` | Kategori penghuni kos (`Putra`, `Putri`, `Campur`) | kategori | Title Case | |
| `status_penyewa` | Status penyewa (`Pekerja`, `Mahasiswa`, `Keluarga`, `Pelajar`) | kategori | Title Case | Variasi `Siswa`, `siswa sma`, `Pelajar SMA`, `Siswa/Pelajar` disatukan ke `Pelajar` |
| `tujuan_utama` | Tujuan aktivitas utama terdekat (`Kampus IT Del`, `Kampus`, `Kantor`, `Sekolah`, `Tidak Disebutkan`) | kategori | Teks | Diekstrak dari jawaban pertanyaan jarak kampus/sekolah/kantor |
| `jarak_*_m` | Jarak menuju 7 fasilitas/lokasi dalam satuan meter | numerik | Meter (`m`) | Input `km` & angka tunggal `1`–`5` dikonversi ke meter (`1,5 km` -> `1500`); typo `300010` -> `3000`; nilai `0` m pada fasilitas publik eksternal (mis. laundry) diimputasi dengan median kecamatan |
| `klasifikasi_jarak_*` | Klasifikasi tingkat kedekatan jarak untuk 7 fasilitas/lokasi | kategori | 4 Kelas | `Sangat Dekat (<= 500 m)`, `Dekat (501 - 1000 m)`, `Sedang (1001 - 3000 m)`, `Jauh (> 3000 m)` |
| `luas_kamar_m2` | Luas kamar kos | numerik | Meter persegi (`m²`) | Format perkalian (`4x4`, `3,5x5`, `4*3`) dihitung otomatis ($P \times L$); input panjang 1 sisi $1,5 \le s \le 4,0$ (`3`, `4 m`) dikonversi ke $s^2$; batas valid kamar kos: $4,0 \le \text{luas} \le 36,0\text{ m}^2$ |
| `jumlah_lantai` | Posisi lantai kamar (numerik) | numerik | Lantai (`1`–`4`) | `bawah tanah` dipetakan ke `1`; lantai di atas `5` (mis. `9`) dipetakan ke `4` |
| `kategori_lantai` | Kategori posisi lantai kamar | kategori | `1`, `2`, `3`, `4 - 5` | Lantai `> 5` dikelompokkan ke dalam kategori `4 - 5` |
| `periode_sewa` | Periode pembayaran sewa (`per bulan` atau `per tahun`) | kategori | Lowercase | |
| `sewa_tahunan` | Penanda kontrak sewa tahunan (`1` = tahunan, `0` = bulanan) | biner | `0` / `1` | |
| `harga_sewa` | Nominal harga sewa sesuai periode pembayaran | numerik | Rupiah (`Rp`, bulat tanpa titik) | Titik pemisah ribuan (`750.000`) dihapus; penulisan singkat (`7`, `250`, `700`, `900`, `10000`, `60000`, `70000`) diskalakan ke nominal Rupiah penuh |
| `harga_bulanan_norm` | Harga sewa ekuivalen bulanan (Target Pemodelan) | numerik | Rupiah/bulan (`Rp`) | Harga tahunan dibagi 12 dan dibulatkan; batas valid logis: $\text{Rp}150.000 \le \text{harga} \le \text{Rp}5.000.000$ |
| `status_harga` | Status keberlakuan harga sewa saat ini | kategori | Teks | `Ya, masih berlaku`, `Tidak, harga sudah berubah`, atau `Kos sudah tidak beroperasi` |
| `biaya_tambahan_rp` | Total biaya tambahan di luar harga sewa | numerik | Rupiah (`Rp`) | Akhiran `rb`/`ribu` (`100rb`) -> `100000`; wajib `0` bila `ada_biaya_tambahan == 'Tidak'`; konsisten dua arah dengan `ada_biaya_tambahan` |

## Variabel Fasilitas & Aturan

| Kolom | Definisi & Standarisasi |
|---|---|
| `ada_dipan`, `ada_kasur`, `ada_lemari`, `ada_meja_belajar`, `ada_tv`, `ada_cermin`, `ada_kulkas_pribadi`, `ada_ventilasi`, `ada_gorden`, `ada_rak_sepatu`, `ada_gantungan_baju` | Ekstraksi biner (`0`/`1`) dari daftar multi-pilih fasilitas di dalam kamar (label kontradiktif `Kamar Kosong` otomatis dihapus bila furnitur tersedia) |
| `ac` | Ketersediaan pendingin ruangan AC (`1` = Ada, `0` = Tidak Ada) |
| `tipe_kamar_mandi`, `km_dalam` | Standarisasi `Dalam` & `Kamar mandi dalam` -> `dalam` (`km_dalam = 1`); `Luar` & `Kamar mandi luar` -> `luar` (`km_dalam = 0`) |
| `kloset_duduk`, `kloset_jongkok`, `ada_shower`, `ada_water_heater`, `ada_bak_mandi`, `ada_gayung` | Ekstraksi biner (`0`/`1`) kelengkapan kamar mandi (pilihan ganda kontradiktif `Toilet duduk, Toilet Jongkok` diselesaikan berdasarkan `km_dalam`) |
| `listrik_termasuk`, `skema_listrik` | Status (`1` = termasuk sewa, `0` = token mandiri) dan teks skema biaya listrik |
| `wifi`, `is_wifi`, `sumber_air`, `fasilitas_dapur`, `fasilitas_cuci_jemur` | Fasilitas bersama dan utilitas kos |
| `keamanan_kos` | Distandarkan menjadi 4 kategori bersih: `CCTV` (menggabungkan `CCTV Saja` dan `CCTV`), `Penjaga/Satpam`, `Penjaga & CCTV`, dan `Tidak Ada` |
| `lahan_parkir` | Distandarkan menjadi `Mobil & Motor` (menggabungkan `Mobil`, `Mobil, Motor`, `Mobil & Motor`), `Motor Saja`, dan `Tidak Ada` |
| `aturan_jam_malam` | Distandarkan menjadi `Bebas 24 Jam` dan `Ada Batas Jam Malam` (menggabungkan `Ada Batas Jam Tertentu`) |
| `kapasitas_kamar` | Kapasitas penghuni kamar (`1 orang`, `2 orang`, `3 orang atau lebih`) |

## Kolom Penilaian Kualitas Data

| Kolom | Definisi |
|---|---|
| `exact_duplicate` | Baris duplikat persis pada seluruh kolom (`0`/`1`) |
| `duplicate_logis` | Baris dengan kesamaan pada `nama_kost`, `kecamatan`, `desa_kelurahan`, `jumlah_lantai`, `luas_kamar_m2`, `periode_sewa`, dan `harga_sewa` (`0`/`1`) |
| `price_anomaly_iqr` | Harga bulanan normalisasi berada di luar batas bawah/atas metode IQR (`Rp175.000` – `Rp1.175.000`) (`0`/`1`) |
| `rejection_reason` | Alasan penolakan baris dari analisis dasar (`bukan entitas kos`, `harga bulanan tidak logis`, `luas kamar tidak logis`, `kos tidak beroperasi`) |
| `accepted_for_analysis` | Baris lolos validasi domain ketat dan kos masih aktif beroperasi (`1` = lolos, total **556 baris**) |
| `model_ready` | Subset konservatif siap pemodelan baseline (`accepted_for_analysis == 1`, `harga_masih_berlaku == 1`, `price_anomaly_iqr == 0`, `duplicate_logis == 0`, total **485 baris**) |
