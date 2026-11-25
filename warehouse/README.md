# Data Warehouse Skema Bintang (`warehouse/`)

Folder ini menjadi sumber kebenaran (*single source of truth*) untuk struktur **Data Warehouse Skema Bintang (Star Schema)** dan Entity-Relationship Diagram (ERD) proyek TobaKost.

## Struktur Artefak Warehouse

- [ddl/star_schema.sql](./ddl/star_schema.sql) — Kontrak DDL tabel fakta (`fact_sewa_kos`), 4 tabel dimensi (`dim_lokasi`, `dim_spesifikasi_kamar`, `dim_fasilitas_aturan`, `dim_kontrak_sewa`), primary/foreign keys, dan view analitik (`vw_mart_kos_lengkap`).
- [erd/star_schema.mmd](./erd/star_schema.mmd) — Diagram ERD dalam format Mermaid.

## Implementasi Warehouse Survei Riil (`data/tobakost_survey_warehouse.db`)

Pipeline `python etl/run_survey_star_schema.py` memuat **923 baris** unit kos aktif yang lolos validasi dasar (`accepted_for_analysis = 1`) dari `data/staging/survey_clean_v1.csv` (sumber `data/raw/Survey_Kos.csv`, 928 baris) ke dalam skema bintang berikut:

1. **`dim_lokasi`:** Menyimpan `id_lokasi` (PK), `kecamatan`, `desa_kelurahan`, `nama_kost`, dan `tujuan_utama`.
2. **`dim_spesifikasi_kamar`:** Menyimpan `id_spesifikasi` (PK), `luas_kamar_m2`, `jumlah_lantai`, `kategori_lantai` (`1`, `2`, `3`, `4 - 5`), `tipe_kamar_mandi` (`dalam`/`luar`), `kelengkapan_kamar_mandi`, `ac`, dan atribut fasilitas kamar biner (`ada_dipan`, `ada_kasur`, `ada_lemari`, `ada_meja_belajar`, `ada_tv`, `ada_cermin`, `ada_kulkas_pribadi`).
3. **`dim_fasilitas_aturan`:** Menyimpan `id_aturan` (PK), `kategori_penghuni`, `status_penyewa`, `keamanan_kos` (`CCTV`, `Penjaga/Satpam`, `Penjaga & CCTV`, `Tidak Ada`), `lahan_parkir`, `aturan_jam_malam`, `kapasitas_kamar`, `skema_listrik`, `listrik_termasuk`, `wifi`, `sumber_air`, `fasilitas_dapur`, dan `fasilitas_cuci_jemur`.
4. **`dim_kontrak_sewa`:** Menyimpan `id_kontrak` (PK), `periode_sewa` (`per bulan`/`per tahun`), dan `sewa_tahunan` (`0`/`1`).
5. **`fact_sewa_kos`:** Menyimpan `id_kost` (PK), `kode_unit_kos`, foreign keys ke keempat dimensi, `harga_sewa`, target `harga_bulanan_norm`, 7 metrik jarak dalam satuan meter (`jarak_*_m`), 7 klasifikasi kedekatan jarak (`klasifikasi_jarak_*`), `biaya_tambahan_rp`, serta flag kualitas (`exact_duplicate`, `duplicate_logis`, `price_anomaly_iqr`, `accepted_for_analysis`, dan `model_ready` = **833 baris**).
6. **`vw_mart_kos_lengkap`:** View denormalisasi hasil join `fact_sewa_kos` dengan keempat tabel dimensi untuk konsumsi langsung oleh modul analitik dashboard dan eksperimen Machine Learning.
