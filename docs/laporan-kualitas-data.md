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
