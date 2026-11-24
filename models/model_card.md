# Model Card

## Status

Model aktif saat ini masih model baseline berbasis data dummy. Jangan menganggap metriknya
sebagai performa pada data riil.

## Ringkasan

- Target: `harga_bulanan_norm`.
- Kandidat: Linear Regression, Ridge, Random Forest, dan Gradient Boosting.
- Artifact model dibuat lokal oleh `python models/train_models.py` dan tidak disimpan di Git.
- Feature engineering: `models/features.py`.
- Metrik: `models/metrics_summary.json`.

## Batasan

- Model terikat pada versi scikit-learn yang tercatat di bundle.
- Data dummy tidak mewakili jaminan performa pada data riil.
- Prediksi adalah estimasi, bukan penetapan harga.
- Model riil harus dibuat sebagai versi baru dengan data quality report dan evaluasi subgroup.

## Fitur dan dataset baseline (Issue #16)

**Target:** `harga_bulanan_norm` (Rp/bulan; harga tahunan sudah dibagi 12).
**Data:** hanya baris `model_ready`. **Split:** 80/20, `random_state=42` (600 baris -> 480 train / 120 test pada data uji).

| Kelompok | Fitur | Alasan |
|---|---|---|
| Ukuran & lantai | `luas_kamar_m2`, `jumlah_lantai` | Spesifikasi fisik langsung memengaruhi tarif |
| Fasilitas (17 biner) | AC, KM dalam, WiFi, parkir mobil, dapur, keamanan, listrik, perabot, kloset duduk, shower, water heater | Inti topik: spesifikasi fasilitas |
| Wilayah | `kecamatan` (one-hot, drop_first) | Beda pasar antar kecamatan |
| Penghuni, air, kapasitas, tempat makan | one-hot, drop_first | Konteks kos |
| Aksesibilitas | 7 kolom `jarak_*` (km) | Inti topik: aksesibilitas lokasi |
| Kontrol kontrak | `is_tahunan` | Harga tahunan/12 berbeda sistematis dari bulanan |

**Tidak dipakai:** `harga_sewa` (kebocoran target), kolom `pred_*`/`selisih_*`/`abs_error`/`status_kewajaran` (hasil model), `skor_kelengkapan_fasilitas` (kombinasi linear persis fasilitas, R2=1.0), `indeks_aksesibilitas_lokasi` (turunan jarak, R2=0.90), `tahun_mulai_sewa`, lat/long, kolom id.

**Catatan:** isi keputusan akhir `is_tahunan` (kontrol vs hanya bulanan) setelah rapat tim.