# Panduan Workflow GitHub Tim

Dokumen ini menjelaskan langkah kerja anggota dan PM dari sinkronisasi branch sampai
perubahan masuk ke `develop` dan `main`.

## Aturan utama

```text
Issue -> branch kerja -> commit -> push -> Pull Request -> review -> merge
```

- `main` adalah branch stabil dan checkpoint.
- `develop` adalah branch integrasi tim.
- Jangan push langsung ke `main` atau `develop`.
- Setiap perubahan harus mengacu pada issue.
- Setiap PR harus direview minimal satu anggota lain.
- Satu branch tugas sebaiknya hanya mengerjakan satu issue atau satu sub-issue.
- Jangan mengubah `data/raw/data_fix.csv` secara langsung.

## Persiapan satu kali

Jalankan di PowerShell:

```powershell
git clone https://github.com/Samuga-14/da-ds-2026-kelompok-10.git
cd da-ds-2026-kelompok-10
git remote -v
```

Pastikan identitas commit menggunakan akun GitHub masing-masing:

```powershell
git config user.name "Nama GitHub"
git config user.email "email-github@example.com"
```

Jika project memakai virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 1. Menentukan issue

Sebelum mulai:

1. Pastikan issue sudah memiliki assignee.
2. Baca tujuan, tugas, path, dependensi, dan kriteria selesai.
3. Pindahkan issue ke `In Progress` pada GitHub Projects.
4. Catat nomor issue untuk branch, commit, dan PR.

Contoh:

```text
Issue #29 - Melatih baseline Linear dan Ridge
```

## 2. Menyamakan branch dengan `develop`

### Cara yang disarankan: membuat branch tugas dari `develop`

```powershell
git fetch origin
git switch develop
git pull --ff-only origin develop
git switch -c ds/29-linear-ridge
```

Contoh nama branch:

```text
ds/29-linear-ridge
ds/36-random-forest-gradient-boosting
da/27-dashboard-summary-service
da/30-distance-analysis
feat/40-prediction-frontend
```

### Jika sudah memiliki branch anggota `develop-1` sampai `develop-5`

Perbarui branch anggota terlebih dahulu:

```powershell
git fetch origin
git switch develop-2
git pull --ff-only origin develop-2
git merge origin/develop
git push origin develop-2
```

Setelah itu, branch tugas dapat dibuat dari branch anggota:

```powershell
git switch develop-2
git switch -c ds/29-linear-ridge
```

Jangan menggunakan branch yang belum disinkronkan karena dapat menyebabkan konflik saat
PR dibuat.

## 3. Menjalankan preprocessing lokal

File staging, laporan kualitas, dan database warehouse dibuat lokal dan tidak disimpan
sebagai file hasil biasa di Git. Setelah branch siap, jalankan:

```powershell
python etl\normalize_survey.py
python etl\run_survey_star_schema.py
```

Untuk memeriksa preprocessing:

```powershell
python -m pytest tests\test_normalize_survey.py -q
```

Output utama:

```text
data/staging/survey_clean_v1.csv
data/quality/survey_quality_v1.json
data/tobakost_survey_warehouse.db
```

File raw tetap menjadi sumber asli:

```text
data/raw/data_fix.csv
```

## 4. Mengerjakan issue

Kerjakan hanya file yang berkaitan dengan issue. Ikuti path yang tercantum di issue.

Sebelum commit, periksa perubahan:

```powershell
git status
git diff --stat
git diff
```

Pastikan tidak ikut ter-commit:

- credential atau `.env`;
- file cache;
- database lokal yang tidak diminta;
- file hasil eksperimen besar;
- perubahan raw data;
- perubahan dari issue lain.

## 5. Membuat commit

Gunakan Conventional Commit dan cantumkan nomor issue:

```powershell
git add models\train_models.py notebooks\04_model_comparison.ipynb
git commit -m "feat: latih baseline linear dan ridge (#29)"
```

Contoh format:

```text
feat: fitur baru atau implementasi
fix: perbaikan bug
data: perubahan ETL atau preprocessing
docs: dokumentasi
test: penambahan atau perbaikan test
refactor: perubahan struktur tanpa mengubah perilaku
```

Jika masih ada pekerjaan lain, buat commit terpisah. Jangan mencampur pekerjaan beberapa
issue dalam satu commit tanpa alasan.

## 6. Push branch ke GitHub

Untuk branch pertama kali:

```powershell
git push -u origin ds/29-linear-ridge
```

Untuk push berikutnya:

```powershell
git push
```

Pastikan branch yang di-push benar:

```powershell
git branch --show-current
git log --oneline -5
```

## 7. Membuat Pull Request

Buat PR melalui GitHub dengan pilihan:

```text
base: develop
compare: branch tugas
```

Contoh:

```text
base: develop
compare: ds/29-linear-ridge
```

Judul PR:

```text
feat: latih baseline linear dan ridge (#29)
```

Isi PR minimal:

```markdown
## Ringkasan
- Jelaskan perubahan yang dibuat.

## Issue
Closes #29

## Path
- `models/train_models.py`
- `notebooks/04_model_comparison.ipynb`

## Validasi
- `python -m pytest tests/test_normalize_survey.py -q`
- Jelaskan hasil test atau eksperimen.

## Catatan
- Jelaskan asumsi, keterbatasan, atau pekerjaan lanjutan.
```

Jika menggunakan GitHub CLI:

```powershell
gh pr create `
  --base develop `
  --head ds/29-linear-ridge `
  --title "feat: latih baseline linear dan ridge (#29)" `
  --body "Closes #29`n`nValidasi: python -m pytest tests/test_normalize_survey.py -q"
```

## 8. Proses review

Setelah PR dibuat:

1. Minta minimal satu anggota lain melakukan review.
2. Pindahkan PR ke status `Review`.
3. Jangan merge PR sendiri sebelum review selesai.
4. Baca setiap komentar reviewer.
5. Perbaiki pada branch yang sama.
6. Push commit perbaikan.
7. Balas komentar dengan penjelasan atau bukti test.

Perubahan setelah review:

```powershell
git add .
git commit -m "fix: tangani masukan review untuk issue #29"
git push
```

PR akan diperbarui otomatis.

## 9. Merge ke `develop`

PM atau maintainer melakukan merge setelah:

- issue sesuai dengan isi PR;
- test atau validasi berhasil;
- minimal satu anggota menyetujui PR;
- tidak ada konflik;
- tidak ada perubahan raw atau secret;
- deskripsi PR dan path bukti sudah lengkap.

Setelah merge, issue akan tertutup otomatis jika PR memakai `Closes #nomor`.

## 10. Menyamakan branch setelah PR di-merge

Setiap anggota harus memperbarui branch lokal:

```powershell
git fetch origin
git switch develop
git pull --ff-only origin develop
```

Jika memiliki branch anggota:

```powershell
git switch develop-2
git pull --ff-only origin develop-2
git merge origin/develop
git push origin develop-2
```

Untuk pekerjaan berikutnya, selalu buat branch baru dari `develop` terbaru. Jangan
melanjutkan branch tugas lama untuk issue berbeda.

## 11. Alur khusus PM: `develop` ke `main`

PR dari `develop` ke `main` dibuat hanya ketika satu checkpoint siap, bukan untuk setiap
commit kecil.

Sebelum membuat PR:

```powershell
git fetch origin
git switch develop
git pull --ff-only origin develop
git switch main
git pull --ff-only origin main
```

Buat PR:

```text
base: main
compare: develop
```

Judul contoh:

```text
chore: integrasikan CP3 ke main
```

Isi PR harus mencantumkan:

- issue dan PR yang termasuk checkpoint;
- hasil test;
- hasil demo;
- perubahan database, API, model, atau dashboard;
- keterbatasan yang masih diketahui.

Setelah PR checkpoint di-merge:

```powershell
git fetch origin
git switch main
git pull --ff-only origin main
git tag v0.3-cp3
git push origin v0.3-cp3
```

Tag hanya dibuat setelah checkpoint selesai dan disetujui tim atau dosen.

## 12. Menangani konflik merge

Jika `git pull` atau `git merge` menimbulkan konflik:

```powershell
git status
```

Buka file konflik, pilih isi yang benar, lalu hapus penanda:

```text
<<<<<<<
=======
>>>>>>>
```

Setelah diperbaiki:

```powershell
git add file-yang-diperbaiki
git commit -m "fix: selesaikan konflik sinkronisasi branch"
git push
```

Jika merge belum selesai dan ingin membatalkan:

```powershell
git merge --abort
```

Jangan menggunakan `git reset --hard` pada branch bersama tanpa persetujuan PM.

## 13. Checklist anggota sebelum meminta merge

- [ ] Issue sudah dipahami dan berstatus `In Progress`.
- [ ] Branch dibuat dari `develop` terbaru.
- [ ] Nama branch memuat area dan nomor issue.
- [ ] Tidak ada perubahan langsung pada `main` atau `develop`.
- [ ] Raw data tidak diubah.
- [ ] Test atau validasi sudah dijalankan.
- [ ] Commit memakai Conventional Commit.
- [ ] Nomor issue tercantum pada commit dan PR.
- [ ] PR menargetkan `develop`.
- [ ] Path file yang diubah tercantum.
- [ ] Minimal satu reviewer sudah diminta.
- [ ] Konflik sudah diselesaikan.

## 14. Checklist PM sebelum merge

- [ ] PR berasal dari branch tugas, bukan push langsung.
- [ ] Issue dan scope PR sesuai.
- [ ] Tidak ada file sensitif atau output lokal yang tidak perlu.
- [ ] Test berhasil.
- [ ] Reviewer sudah menyetujui.
- [ ] Perubahan lintas area dijelaskan.
- [ ] Status issue dan Projects diperbarui.
- [ ] Setelah beberapa issue selesai, `develop` siap dipromosikan ke `main`.
