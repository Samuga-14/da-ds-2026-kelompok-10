# Laporan Minggu 11

Salin template dari `minggu-01.md`, lalu isi CP4, API model, dan integrasi prototipe.


# Laporan Minggu 14

## Topik

Finalisasi EDA survei, laporan hasil eksplorasi, visualisasi dashboard, dan dokumentasi
penyerahan Issue #15.

## Issue

- #15 — Membuat EDA dan visualisasi kualitas data survey

## Tujuan

Menjawab seluruh kebutuhan EDA dengan data staging dan warehouse survei:

- distribusi harga bulanan normalisasi;
- harga berdasarkan kecamatan dan kategori penghuni;
- distribusi luas kamar dan lantai;
- hubungan fasilitas dengan harga;
- hubungan jarak fasilitas dengan harga;
- visualisasi missing, outlier, dan status data;
- interpretasi pada setiap grafik.

## Pekerjaan yang Diselesaikan

- Menjalankan ulang ETL survei tanpa mengubah raw data.
- Memperbarui `notebooks/02_eda_survey.ipynb` agar mencakup seluruh tugas EDA.
- Memastikan staging berisi 328 baris dan warehouse survei memuat 312 baris fact.
- Menyimpan kandidat duplikasi, outlier, dan status model sebagai flag.
- Membuat laporan tertulis pada `docs/laporan-eda.md`.
- Menyediakan grafik EDA pada halaman dashboard Fasilitas & Keamanan.

## Temuan Utama

- Median harga setara bulanan pada subset analisis adalah Rp687.500.
- Ada 25 kandidat outlier IQR dan 30 baris terlibat duplikasi logis.
- Ada 312 baris lolos analisis dasar dan 260 baris `model_ready`.
- `tahun_mulai_menyewa` kosong pada seluruh baris staging karena sumber saat ini tidak menyediakan data.
- Lantai 9 dan lantai 3 hanya masing-masing berisi satu baris sehingga belum cukup untuk generalisasi.

## Bukti Teknis

```text
python etl/normalize_survey.py
python etl/run_survey_star_schema.py
python -m unittest tests/test_normalize_survey.py -v
```

Hasil validasi:

- 328 baris raw dan staging;
- 312 fact pada warehouse survei;
- 260 baris model-ready;
- 25 kandidat outlier IQR;
- 2 test normalisasi lulus.
