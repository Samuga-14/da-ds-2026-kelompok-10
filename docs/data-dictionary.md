# Data Dictionary

Dataset: `data/raw/data_fix.csv`

Raw survey tidak diubah oleh pipeline. Output staging dibuat oleh
`python etl/normalize_survey.py` di `data/staging/survey_clean_v1.csv`.
Laporan kualitas tersedia di `data/quality/survey_quality_v1.json`.

## Variabel Utama

| Kolom staging | Definisi | Tipe | Catatan |
|---|---|---|---|
| `nama_kost` | Nama kos yang ditinggali responden | string | Bukan kunci unik unit |
| `kecamatan` | Kecamatan lokasi kos | kategori | Dinormalisasi dengan title case |
| `desa_kelurahan` | Desa atau kelurahan kos | kategori | |
| `kategori_penghuni` | Putra, putri, atau campur | kategori | |
| `status_penyewa` | Mahasiswa, pekerja, keluarga, atau pelajar | kategori | Nilai variasi perlu dinormalisasi lanjutan |
| `jarak_*_m` | Jarak menuju fasilitas dalam meter | numerik | Parsing dari jawaban Google Form |
| `luas_kamar_m2` | Luas kamar dalam meter persegi | numerik | Nilai `<= 0` atau `> 100` ditandai tidak valid |
| `jumlah_lantai` | Posisi lantai kamar | numerik | Nilai selain 1-3 perlu ditinjau |
| `periode_sewa` | Per bulan atau per tahun | kategori | |
| `harga_sewa` | Harga sesuai periode yang dipilih | numerik | Belum dinormalisasi |
| `harga_bulanan_norm` | Harga setara bulanan | numerik | Harga tahunan dibagi 12 |
| `status_harga` | Status harga masih berlaku atau tidak | kategori | |
| `model_ready` | Layak dipakai baseline model | boolean | Hanya baris tanpa reject, anomaly, dan duplikasi logis |

## Variabel Fasilitas

| Kolom | Definisi |
|---|---|
| `ada_dipan`, `ada_kasur`, `ada_lemari`, `ada_meja_belajar`, `ada_tv`, `ada_cermin`, `ada_kulkas_pribadi` | Ekstraksi biner dari daftar fasilitas kamar |
| `ac` | Ada atau tidak ada pendingin ruangan |
| `tipe_kamar_mandi` | Kamar mandi dalam atau luar |
| `kloset_duduk`, `kloset_jongkok`, `ada_shower`, `ada_water_heater` | Ekstraksi biner kelengkapan kamar mandi |
| `listrik_termasuk`, `skema_listrik` | Status dan skema biaya listrik |
| `wifi`, `sumber_air`, `fasilitas_dapur`, `fasilitas_cuci_jemur` | Fasilitas bersama dan utilitas |
| `keamanan_kos`, `lahan_parkir`, `aturan_jam_malam`, `kapasitas_kamar` | Fasilitas dan aturan hunian |

## Kolom Penilaian Kualitas

| Kolom | Definisi |
|---|---|
| `exact_duplicate` | Baris duplikat persis |
| `duplicate_logis` | Baris yang sama pada nama, wilayah, lantai, luas, periode, dan harga |
| `price_anomaly_iqr` | Harga normalisasi berada di luar batas IQR |
| `rejection_reason` | Alasan baris ditolak dari analisis utama |
| `accepted_for_analysis` | Baris lolos validasi dasar |
| `model_ready` | Baris layak dipakai model baseline |

Perubahan threshold atau aturan preprocessing harus dicatat pada commit, report kualitas,
dan laporan mingguan sebagai metode yang dapat direproduksi.
