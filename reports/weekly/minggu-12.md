# Laporan Mingguan - Kelompok 10 - Minggu ke-12

**Periode:** 21/11–27/11/2026<br>
**Status:** Kuning

> Commit dihitung tanpa merge/sinkronisasi. Jam kerja dan progres jurnal tidak tercatat di GitHub.

## 1. Target vs capaian

| Target | Capaian | Bukti |
|---|---|---|
| Data Readiness dan dokumentasi CP2 (survei 928 baris) | Selesai; 923 baris masuk warehouse, 833 siap model | [PR #65](https://github.com/Samuga-14/da-ds-2026-kelompok-10/pull/65)<br>[Rilis #66](https://github.com/Samuga-14/da-ds-2026-kelompok-10/pull/66) |
| Integrasi warehouse, analisis harga/fasilitas, storytelling | Selesai | [PR #67](https://github.com/Samuga-14/da-ds-2026-kelompok-10/pull/67)<br>[Rilis #68](https://github.com/Samuga-14/da-ds-2026-kelompok-10/pull/68) |
| API ringkasan dashboard dan model registry | Selesai | [PR #49](https://github.com/Samuga-14/da-ds-2026-kelompok-10/pull/49)<br>[PR #50](https://github.com/Samuga-14/da-ds-2026-kelompok-10/pull/50) |
| Analisis pengaruh fasilitas kamar | Sebagian; ada commit, issue masih terbuka | [Commit analisis](https://github.com/Samuga-14/da-ds-2026-kelompok-10/commit/ee8cacd0f5a497c02f126fc5d0af2b683fe7f04e)<br>[Issue #26](https://github.com/Samuga-14/da-ds-2026-kelompok-10/issues/26) |
| Evaluasi baseline Linear/Ridge | Sebagian; metrik belum terverifikasi | [Commit baseline](https://github.com/Samuga-14/da-ds-2026-kelompok-10/commit/6ae6fce0d5346ef5e97906525b20262c93bb6e09)<br>[Issue #29](https://github.com/Samuga-14/da-ds-2026-kelompok-10/issues/29) masih terbuka |
| Deployment dan uji kegunaan 3–5 pengguna | Belum terverifikasi | Belum ditemukan bukti deployment atau hasil UAT |

## 2. Kontribusi anggota

| Anggota | Commit* | Kontribusi | Bukti | Jam |
|---|---:|---|---|---|
| Samuga Hutagaol | 8 | Preprocessing 928 baris, dokumentasi CP2, integrasi warehouse/analytics | [PR #56](https://github.com/Samuga-14/da-ds-2026-kelompok-10/pull/56)<br>[PR #63](https://github.com/Samuga-14/da-ds-2026-kelompok-10/pull/63)<br>[PR #65](https://github.com/Samuga-14/da-ds-2026-kelompok-10/pull/65)<br>[PR #67](https://github.com/Samuga-14/da-ds-2026-kelompok-10/pull/67) | Belum tercatat |
| Intan Siregar | 3 | Split/fitur baseline dan loader model registry beserta uji loader | [PR #48](https://github.com/Samuga-14/da-ds-2026-kelompok-10/pull/48)<br>[PR #50](https://github.com/Samuga-14/da-ds-2026-kelompok-10/pull/50) | Belum tercatat |
| Epelina Pangaribuan | 2 | EDA/visualisasi kualitas data dan analisis fasilitas | [PR #51](https://github.com/Samuga-14/da-ds-2026-kelompok-10/pull/51)<br>[Issue #26](https://github.com/Samuga-14/da-ds-2026-kelompok-10/issues/26) | Belum tercatat |
| Esthefany Sipahutar | 1 | Melatih baseline Linear dan Ridge; evaluasi belum selesai | [Commit baseline](https://github.com/Samuga-14/da-ds-2026-kelompok-10/commit/6ae6fce0d5346ef5e97906525b20262c93bb6e09)<br>[Issue #29](https://github.com/Samuga-14/da-ds-2026-kelompok-10/issues/29) | Belum tercatat |
| Novsiana Silalahi | 1 | Sinkronisasi filter dashboard dengan API ringkasan | [PR #49](https://github.com/Samuga-14/da-ds-2026-kelompok-10/pull/49)<br>[Commit filter](https://github.com/Samuga-14/da-ds-2026-kelompok-10/commit/7c2b62ee5ec8b9f3ee8ea2793c763433541683ee) | Belum tercatat |

## 3. Metrik minggu ini
- Commit anggota (non-merge): **15**
- PR di-merge: **15** (#41, #48–#53, #56, #57, #63–#68; termasuk sinkronisasi/rilis)
- Issue ditutup: **12** (#7–#11, #13, #15–#17, #27, #31, #54)
- Pengujian: **11** uji unit loader dan **22** uji unit integrasi analytics lulus.
- Metrik model: MAE/RMSE/MAPE/R² baseline baru belum tercatat; Issue #29 masih terbuka.

## 4. Progres jurnal

| Bagian | Penanggung jawab | Progres |
|---|---|---|
| Naskah jurnal | Belum teridentifikasi dari commit/issue minggu ini | Belum tercatat |

## 5. Kendala dan bantuan
- Issue analisis fasilitas #26 dan evaluasi baseline #29 masih terbuka.
- Bukti deployment dan uji kegunaan 3–5 pengguna belum ditemukan.
- Tidak ada permintaan bantuan dosen yang tercatat. Jam kerja dan progres jurnal perlu dikonfirmasi.

## 6. Rencana minggu depan
Rencana berikut berdasarkan issue terbuka dan arahan umum minggu ke-13; pembagian tugas final belum tercatat.

| Anggota | Rencana | Issue |
|---|---|---|
| Samuga Hutagaol | Koordinasikan laporan akhir dan code freeze | [#62](https://github.com/Samuga-14/da-ds-2026-kelompok-10/issues/62) |
| Intan Siregar | Validasi integrasi loader/prediksi dan dokumentasikan hasil | [#62](https://github.com/Samuga-14/da-ds-2026-kelompok-10/issues/62) |
| Epelina Pangaribuan | Rampungkan interpretasi analisis fasilitas dan perbaikan EDA/UI | [#26](https://github.com/Samuga-14/da-ds-2026-kelompok-10/issues/26), [#62](https://github.com/Samuga-14/da-ds-2026-kelompok-10/issues/62) |
| Esthefany Sipahutar | Lengkapi evaluasi dan catat MAE, RMSE, MAPE, R² | [#29](https://github.com/Samuga-14/da-ds-2026-kelompok-10/issues/29) |
| Novsiana Silalahi | Uji dashboard/API dan dokumentasikan hasil kegunaan | [#62](https://github.com/Samuga-14/da-ds-2026-kelompok-10/issues/62) |

*Commit adalah commit non-merge yang diatribusikan kepada anggota.
