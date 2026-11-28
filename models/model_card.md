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
**Data:** hanya baris `model_ready`. **Split:** 80/20, `random_state=42` (485 baris -> 388 train / 97 test).

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

## Interpretasi Analisis Kewajaran Harga

Dashboard analitik membandingkan `harga_bulanan_norm` dengan prediksi Random Forest (`pred_rf`). Selisih persentase dihitung dengan rumus:

`((harga_bulanan_norm - pred_rf) / pred_rf) * 100`

Kategori ditentukan menggunakan ambang 6%:
- Di bawah -6%: `Underpriced (Sangat Hemat)`.
- Dari -6% sampai +6%, termasuk batasnya: `Fair Price (Harga Wajar)`.
- Di atas +6%: `Overpriced (Kemahalan)`.

Kategori tersebut menunjukkan perbandingan harga aktual terhadap prediksi model, bukan bukti mutlak bahwa harga kos murah atau mahal di pasar. Model masih berbasis data dummy, sehingga hasilnya bersifat ilustratif dan perlu divalidasi dengan data riil.

**Perbedaan dengan kalkulator API:** analitik dashboard menggunakan prediksi Random Forest untuk menentukan label kewajaran, sedangkan kalkulator API menggunakan model terpilih berdasarkan MAE pada test set. Label analitik tidak sama dengan hasil atau rentang estimasi kalkulator API.