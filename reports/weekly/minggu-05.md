# Laporan Mingguan - Kelompok 10 - Minggu ke-05 (CP2 Data Readiness)
Periode : 18/11 - 25/11/2026  
Status  : Hijau  

## 1. Target vs capaian
| Target minggu ini (CP2 Data Readiness) | Status (selesai/sebagian/belum) | Bukti |
|---|---|---|
| Akuisisi & preprocessing dataset survei kos Kabupaten Toba (`Survey_Kos.csv`, 928 baris) | **Selesai** | Issue #11, #13, #14, #54 / PR #12, #23, #56, #57 |
| Pembangunan Data Warehouse Skema Bintang (`tobakost_survey_warehouse.db`, 923 fact rows) | **Selesai** | `etl/run_survey_star_schema.py`, `warehouse/ddl/star_schema.sql`, `warehouse/erd/star_schema.mmd` |
| EDA & visualisasi kualitas data 928 baris beserta 5 temuan utama | **Selesai** | Issue #15 / PR #51, `notebooks/02_eda_survey.ipynb`, `docs/laporan-eda.md` |
| Penentuan fitur kandidat & reproducible train-test split (`random_state=42`) | **Selesai** | Issue #16 / `models/features_candidate.py`, `notebooks/03_feature_engineering.ipynb` |
| Dokumentasi Data Dictionary & Laporan Kualitas Data 4 Dimensi | **Selesai** | Issue #17 / `docs/data-dictionary.md`, `docs/laporan-kualitas-data.md`, `data/quality/survey_quality_v1.json` |

## 2. Kontribusi anggota
| Nama | Tugas | Tautan commit/PR/issue | Jam kerja |
|---|---|---|---|
| Samuel Bona Tua Hutagaol (`Samuga-14`) | Pipeline preprocessing 928 baris (`normalize_survey.py`), star schema warehouse (`run_survey_star_schema.py`), unit test, dan sertifikasi kualitas CP2 | Issue #11, #14, #54 / PR #12, #23, #56, #57 | 10 jam |
| Epelina Pangaribuan (`EpelinaPangaribuan`) | Exploratory Data Analysis (EDA), 6 kelompok visualisasi kualitas & distribusi harga/fasilitas/jarak, laporan 5 temuan utama | Issue #15 / PR #51 (`notebooks/02_eda_survey.ipynb`, `docs/laporan-eda.md`) | 8 jam |
| Intan Sonia Siregar (`intansrg30`) | Evaluasi kelayakan fitur kandidat, pencegahan data leakage, encoding fitur, dan reproducible split 80/20 | Issue #16 / Commit `e5e88db` (`models/features_candidate.py`, `notebooks/03_feature_engineering.ipynb`) | 8 jam |
| Novsiana Silalahi (`NovsianaSilalahi`) | Penyusunan Data Dictionary, dokumentasi kualitas data CP2, dan service ringkasan statistik warehouse | Issue #17, #27 / PR #49 (`docs/data-dictionary.md`, `data/README.md`, `services/analytics_service.py`) | 8 jam |
| Esthefany Christin Sipahutar (`esthefanysipahutar`) | Peninjauan skema fitur regresi dan persiapan eksperimen baseline model CP3 | Issue #18, #29 (`models/train_models.py`, `models/model_card.md`) | 6 jam |

## 3. Metrik minggu ini
- **Dataset Survei Riil (`Survey_Kos.csv`):** 928 baris mentah (35 kolom) $\rightarrow$ 928 baris staging (74 kolom, **0 sel kosong**).
- **Warehouse & Model Readiness:** **923 baris** lolos ke `fact_sewa_kos` (`tobakost_survey_warehouse.db`), **833 baris** berstatus `model_ready = 1`, 42 baris duplikasi logis, 42 kandidat outlier IQR (`Rp229.687,50` – `Rp1.142.187,50`).
- **Pengujian Otomatis:** 8 unit test preprocessing lulus (`python -m unittest tests/test_normalize_survey.py -v`) & 11 unit test model loader lulus (`tests/test_model_loader.py`).

## 4. Progres jurnal
| Bagian naskah | Penanggung jawab | % selesai |
|---|---|---:|
| Ide judul, rumusan masalah, & kontribusi dataset lokal Toba | `Samuga-14`, `EpelinaPangaribuan` | 100% |
| Draf Pendahuluan & Tinjauan Pustaka | `EpelinaPangaribuan`, `NovsianaSilalahi` | 60% |
| Draf Metode: Akuisisi Data, Preprocessing 4 Dimensi, & Star Schema ETL | `Samuga-14`, `intansrg30`, `esthefanysipahutar` | 80% |

## 5. Kendala dan bantuan yang dibutuhkan
- Variasi input responden pada kuesioner Google Form (seperti penulisan luas kamar `4x4`, satuan jarak campuran `km` dan `m`, penulisan singkat harga `7` atau `700`, serta kategori `CCTV Saja` vs `CCTV`) telah berhasil diatasi seluruhnya secara terprogram di `etl/normalize_survey.py`.

## 6. Rencana minggu depan (Menuju CP3 Checkpoint Tengah)
| Nama | Rencana tugas | Issue |
|---|---|---|
| `esthefanysipahutar` | Melatih & membandingkan 4 model regresi (Linear, Ridge, Random Forest, Gradient Boosting) dengan K-Fold CV & Tuning pada 833 baris `model_ready` | Issue #18, #29, #36, #38 |
| `NovsianaSilalahi` | Menghubungkan Dashboard v1, filter global, dan visualisasi distribusi/hierarki harga ke warehouse survei 923 baris | Issue #19, #32, #37, #44 |
| `EpelinaPangaribuan` | Analisis mendalam pengaruh fasilitas kamar, keamanan, dan korelasi/pemetaan jarak (meter) terhadap tarif | Issue #20, #26, #30, #34, #43, #47 |
| `intansrg30` | Menyelesaikan endpoint REST API prediksi (`POST /api/predict`) dan integrasi kalkulator harga ke frontend | Issue #21, #35, #40 |
| `Samuga-14` | Evaluasi klasifikasi harga wajar (*Underpriced/Fair/Overpriced*), simulasi penambahan fasilitas, dan orkestrasi ETL otomatis | Issue #22, #28, #33, #39, #42 |
