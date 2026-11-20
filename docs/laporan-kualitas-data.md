# Laporan Kualitas Data Survei Kos Toba

## Ringkasan

Dataset mentah yang dianalisis adalah `data/raw/data_fix.csv` dengan 328 baris dan
44 kolom. File raw tidak diubah. Pipeline preprocessing menghasilkan staging pada
`data/staging/survey_clean_v1.csv` dan laporan terstruktur pada
`data/quality/survey_quality_v1.json`.

## Temuan Utama

| Pemeriksaan | Hasil |
|---|---:|
| Exact duplicate | 0 |
| Duplikasi logis | 30 baris terlibat |
| Kandidat outlier IQR | 25 |
| Lolos analisis dasar | 313 |
| `model_ready` | 261 |
| Baris ditolak atau kos tidak aktif | 15 |

## Duplikasi

Exact duplicate tidak ditemukan. Duplikasi logis didefinisikan berdasarkan kesamaan
nama kos, kecamatan, desa/kelurahan, lantai, luas kamar, periode sewa, dan harga.
Duplikasi logis diberi flag, tetapi tidak langsung dihapus. Nama kos sama tidak dianggap
duplikat jika kombinasi unit atau fasilitas berbeda.

## Harga dan Outlier

Harga tahunan dikonversi menjadi setara bulanan dengan pembagian 12. Harga bulanan
dipertahankan tanpa konversi.

Metode IQR menghasilkan batas:

```text
Batas bawah: Rp128.125
Batas atas: Rp1.253.124
```

Hasil IQR hanya sebagai kandidat review. Outlier dapat berupa kesalahan penulisan,
harga tahunan yang tidak dikonversi, atau unit dengan karakteristik premium. Baris
outlier harus ditinjau dari kombinasi luas, lantai, fasilitas, lokasi, dan periode sewa
sebelum dihapus.

## Nilai Tidak Valid

Baris ditolak dari analisis dasar bila:

- harga setara bulanan di luar Rp100.000 sampai Rp20.000.000;
- luas kamar tidak positif atau lebih dari 100 m2;
- kos dinyatakan tidak beroperasi.

Tidak ada exact duplicate. Sebanyak 15 baris berada pada rejection atau status kos tidak
aktif.

## Missing Value

Pemeriksaan staging menunjukkan missing utama pada:

- `tahun_mulai_menyewa`, karena kolom sumber tidak tersedia pada dataset saat ini;
- satu baris dengan jarak kampus/sekolah/tempat kerja kosong;
- satu baris dengan lantai kosong.

Missing tidak boleh diganti sembarang dengan rata-rata. Untuk baseline model,
baris dengan variabel target atau fitur kunci kosong perlu dipisahkan dan diberi
flag.

## Status Siap Model

`model_ready` hanya digunakan untuk subset konservatif baseline. Baris harus:

- lolos validasi dasar;
- harga masih berlaku;
- bukan kandidat outlier IQR;
- bukan duplikasi logis.

Dataset staging tetap mempertahankan semua 328 baris beserta kolom flag. Pemisahan
dataset untuk model tidak dilakukan dengan penghapusan permanen pada file raw.

## Review dan Sertifikasi CP2

Pemeriksaan ulang pipeline dilakukan pada 19 November 2026 menggunakan dataset
`data/raw/data_fix.csv`. Hasil eksekusi menghasilkan 328 baris staging dari 44
kolom sumber, sehingga file raw tetap tidak diubah.

| Keputusan review | Hasil |
|---|---:|
| Baris ditolak atau kos tidak aktif ditinjau | 15 |
| Baris yang memiliki duplikasi logis ditandai | 30 |
| Kandidat outlier IQR ditandai untuk review | 25 |
| Target model yang disetujui | `harga_bulanan_norm` |
| Baris fact pada warehouse | 313 |
| Baris `model_ready` | 261 |

Keputusan final:

1. Tidak ada exact duplicate yang perlu dihapus.
2. Duplikasi logis dan kandidat outlier tidak dihapus dari staging; keduanya tetap
   tersedia melalui flag untuk audit dan analisis lanjutan.
3. Harga tahunan dikonversi ke ekuivalen bulanan, sedangkan harga bulanan
   dipertahankan.
4. Baseline model hanya boleh menggunakan baris dengan `model_ready = 1`.
5. Warehouse hanya memuat 313 baris yang lolos validasi dasar, tanpa mengubah
   dataset raw.

Validasi teknis yang dijalankan:

```text
python -m pytest tests/test_normalize_survey.py -q
2 passed

python etl/normalize_survey.py
raw_rows=328, staging_rows=328, exact_duplicates=0
logical_duplicate_rows=30, price_anomaly_iqr=25
accepted_for_analysis=313, model_ready=261

python etl/run_survey_star_schema.py
Fact rows: 313
Model-ready rows: 261
```
