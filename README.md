# LMS AI — Sistem Penilaian Jawaban Esai dengan Kecerdasan Buatan

Sistem **Learning Management System (LMS)** berbasis web untuk mengelola ujian esai dan menilai jawaban siswa secara otomatis menggunakan model NLP (Natural Language Processing) yang dijalankan **lokal/offline** melalui runtime **ONNX** dan antrean tugas asinkron **Celery + Redis**.

> Dikembangkan pertama kali oleh **Athailah, S.Kom, MOS** dan dirilis sebagai proyek **open source** di bawah lisensi [MIT](LICENSE).

---

## Fitur Utama

- **Manajemen Kursus & Ujian** — kursus, ujian, soal esai, dan kunci jawaban dikelola lewat Django Admin.
- **Penilaian AI Real** — jawaban esai dibandingkan dengan kunci jawaban melalui **cosine similarity embedding** dari model `paraphrase-multilingual-MiniLM-L12-v2` (diolah menjadi ONNX), berjalan **offline** tanpa API pihak ketiga.
- **Pemrosesan Asinkron** — penilaian dijalankan di latar belakang oleh Celery, halaman siswa tidak membeku.
- **Dashboard Instruktur** — tinjau skor & feedback AI, simpan skor akhir (validasi siswa), dan **Proses Ulang** untuk penilaian yang gagal/terhambat.
- **Kontrol Akses Berbasis Role**:
  - **Student** — hanya dapat mengerjakan soal pada kursus yang di-*enroll* (403 jika belum terdaftar).
  - **Teacher** — hanya dapat melihat kursus, ujian, soal, dan penilaian dari kursus yang **diajarkannya** (data guru lain diisolasi).
  - **Staff/Superuser** — akses penuh ke semua data.
- **Tampilan Responsif** dengan **Tailwind CSS** (build statis, tidak bergantung CDN — tampil konsisten saat offline).
- **Antrian Fleksibel** — command `reprocess_pending` untuk memproses ulang penilaian `PENDING`/`FAILED`.

---

## Teknologi

| Lapisan | Teknologi |
| --- | --- |
| Backend | Django 6, Celery 5 |
| Database | PostgreSQL (psycopg 3) |
| Message Broker | Redis (via Memurai di Windows) |
| AI / NLP | ONNX Runtime, Transformers, `paraphrase-multilingual-MiniLM-L12-v2` |
| Frontend | Tailwind CSS (build statis via Node/npm) |

---

## Struktur Proyek

```
lms_ai_project/
├── lms_core/              # Konfigurasi Django utama (settings, urls, celery)
├── lms_app/               # Aplikasi LMS (model, views, tugas, template, command)
│   ├── management/commands/
│   │   ├── seed_data.py           # Seed role, user, kursus, enroll, pengajaran
│   │   └── reprocess_pending.py   # Proses ulang penilaian PENDING/FAILED
│   └── templates/lms_app/         # Template Tailwind (base, beranda, dashboard, dll)
├── ai_grader/             # Engine AI (ONNX): embedding & cosine similarity
├── static/                # Tailwind source & output CSS
├── model_onnx/            # Model ONNX + tokenizer (TIDAK di-commit ke git)
├── export_model_onnx.py   # Skrip ekspor model HuggingFace → ONNX
├── manage.py
├── requirements.txt
├── package.json           # Script npm untuk build Tailwind
└── LICENSE / README.md
```

---

## Prasyarat

- **Python** 3.12+
- **Node.js** 18+ (untuk build Tailwind)
- **PostgreSQL** 12+
- **Redis** — di Windows gunakan [Memurai](https://www.memurai.com/) atau Redis versi port Windows (service di port `6379`)

---

## Instalasi & Setup

1. **Clone & masuk folder**
   ```bash
   git clone https://github.com/tuxkeren/lms_ai_project.git
   cd lms_ai_project
   ```

2. **Buat virtual environment & install dependensi**
   ```bash
   python -m venv venv
   venv\Scripts\activate          # Windows (PowerShell/cmd)
   # source venv/bin/activate     # Linux/macOS
   pip install -r requirements.txt
   npm install
   ```

3. **Konfigurasi environment**
   ```bash
   copy .env-example .env        # Windows
   # cp .env-example .env        # Linux/macOS
   ```
   Edit `.env` — sesuaikan `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `SECRET_KEY`, `DEBUG`.

4. **Siapkan database & migration**
   ```bash
   python manage.py migrate
   ```

5. **Siapkan model AI (ONNX)**

   Model terletak di folder `model_onnx/` yang tidak ikut di-commit (besar). Ekspor ulang dari HuggingFace:
   ```bash
   # Windows: wajib atur encoding UTF-8 agar karakter emoji/non-ASCII tidak error
   $env:PYTHONIOENCODING = 'utf-8'
   python export_model_onnx.py
   ```
   Script akan menyimpan `model.onnx` (+ file data) dan tokenizer ke `model_onnx/`.

6. **Build Tailwind CSS** (jalankan ulang bila menambah class baru di template)
   ```bash
   npm run build                 # sekali
   npm run dev                   # mode watch (auto rebuild)
   ```

7. **Seed data awal (opsional tetapi disarankan)**
   ```bash
   python manage.py seed_data --uji-contoh
   ```
   Membuat group `Student` & `Teacher`, user demo (lihat tabel di bawah), kursus, enroll, penugasan guru, dan ujian contoh (dengan `--uji-contoh`).

---

## Menjalankan Aplikasi

Jalankan **dua terminal**:

```bash
# Terminal 1 — Web server
venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000

# Terminal 2 — Celery worker (Windows wajib --pool=solo)
venv\Scripts\python.exe -m celery -A lms_core worker --loglevel=info --pool=solo
```

Buka **http://127.0.0.1:8000** — login melalui halaman **Masuk** (`/masuk/`), admin di **/admin/**.

> Pastikan Redis berjalan di `127.0.0.1:6379`. Jika Celery/Redis mati, kirim jawaban tetap aman: task masuk status `FAILED` dengan pesan, dan dapat diproses ulang lewat tombol **Proses Ulang** di dashboard.

---

## Akun Demo (hasil seed)

| Username | Password | Role | Kursus |
| --- | --- | --- | --- |
| `student01` | `student123` | Student | Fisika Dasar |
| `student02` | `student123` | Student | Bahasa Inggris |
| `student03` | `student123` | Student | Matematika Dasar (ujian contoh) |
| `guru01` | `teacher123` | Teacher | Fisika Dasar |
| `guru02` | `teacher123` | Teacher | Bahasa Inggris |
| `guru03` | `teacher123` | Teacher | Matematika Dasar |

---

## Management Command

```bash
python manage.py seed_data [--jumlah-siswa 5] [--password ...] [--jumlah-guru 4] [--password-guru ...] [--uji-siswa-pertama] [--uji-contoh]
python manage.py reprocess_pending [--ids 1 2 3]      # proses ulang semua PENDING/FAILED, atau id tertentu
```

---

## Menjalankan Test

```bash
python manage.py test --noinput
```

> Suite berjumlah 26+ test. Catatan: pada Postgres lokal, suite berjalan kasar ±3–6 menit.

---

## Lisensi

Proyek ini dirilis di bawah **MIT License**. Lihat file [LICENSE](LICENSE) untuk detail lengkap.

Copyright © 2026 **Athailah, S.Kom, MOS**

Anda bebas menggunakan, memodifikasi, dan mendistribusikan ulang dengan tetap mencantumkan pemberitahuan hak cipta di atas.