# 📚 StudyMate AI — Intelligent RAG-Powered PDF Study Assistant

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.12+"/>
  <img src="https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/Google_Gemini-2.0_Flash-4285F4?style=for-the-badge&logo=google&logoColor=white" alt="Google Gemini"/>
  <img src="https://img.shields.io/badge/ChromaDB-Vector_Store-FF6F00?style=for-the-badge" alt="ChromaDB"/>
  <img src="https://img.shields.io/badge/Embeddings-all--MiniLM--L6--v2-blue?style=for-the-badge" alt="Embeddings"/>
  <img src="https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker Compose"/>
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="MIT License"/>
</p>

<p align="center">
  <strong>Asisten belajar cerdas bertenaga Retrieval-Augmented Generation (RAG)</strong><br/>
  Unggah Buku Teks PDF ➔ Ajukan Pertanyaan dengan Sitasi Halaman Akurat ➔ Hasilkan Kuis, Flashcard & Rencana Belajar
</p>

<p align="center">
  <a href="#-fitur-utama">Fitur Utama</a> •
  <a href="#-arsitektur-rag">Arsitektur RAG</a> •
  <a href="#-teknologi--stack">Tech Stack</a> •
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-spesifikasi-api">API Docs</a> •
  <a href="#-pengujian-testing">Testing</a> •
  <a href="#-deployment">Deployment</a>
</p>

---

## ✨ Fitur Utama

| Fitur | Deskripsi | Status |
|---|---|:---:|
| 🔐 **Autentikasi JWT Terenkripsi** | Registrasi & Login aman dengan enkripsi password BCrypt dan JSON Web Tokens | ✅ Lengkap |
| 📄 **Upload & Parsing PDF** | Ekstraksi teks multi-halaman berkinerja tinggi menggunakan PyMuPDF | ✅ Lengkap |
| ⚡ **Pipeline Pemrosesan AI** | Segmentasi teks cerdas ➔ Embedding vektor ➔ Pengindeksan ChromaDB | ✅ Lengkap |
| 🔍 **Pencarian Semantik** | Pencarian teks berbasis makna (*cosine similarity*) melintasi seluruh buku | ✅ Lengkap |
| 💬 **Asisten Chat RAG** | Tanya jawab cerdas berbasis konteks buku dengan sitasi halaman spesifik `[Page X]` | ✅ Lengkap |
| 📑 **Ringkasan Otomatis & Ekspor PDF** | Ringkasan 5 poin kunci dengan dukungan unduh dokumen PDF via ReportLab | ✅ Lengkap |
| 📝 **Generator Kuis Interaktif** | Pembuatan kuis pilihan ganda otomatis dengan penilaian dan penjelasan jawaban | ✅ Lengkap |
| 🎴 **Flashcard Interaktif 3D** | Kartu hafalan interaktif dengan efek balik 3D (*flip card*) | ✅ Lengkap |
| 📅 **Generator Rencana Belajar** | Jadwal belajar harian yang dipersonalisasi sesuai target hari pengguna | ✅ Lengkap |
| 🛡️ **Rate Limiter & Hardening** | Proteksi 60 req/menit per IP, validasi skema Pydantic, dan isolasi data per pengguna | ✅ Lengkap |

---

## 🏗️ Arsitektur RAG

StudyMate AI mengimplementasikan arsitektur **Retrieval-Augmented Generation (RAG)** asinkron:

```
┌─────────────────┐
│ Unggah Buku PDF │
└────────┬────────┘
         ▼
┌─────────────────────────────────┐
│ Ekstraksi Teks (PyMuPDF)        │
└────────┬────────────────────────┘
         ▼
┌─────────────────────────────────┐
│ Pemecahan Chunk (RecursiveSplit)│
└────────┬────────────────────────┘
         ▼
┌─────────────────────────────────┐
│ Embedding (all-MiniLM-L6-v2)    │
└────────┬────────────────────────┘
         ▼
┌─────────────────────────────────┐
│ Simpan di Vector DB (ChromaDB)  │
└────────┬────────────────────────┘
         │
         │  ◄── [Pengguna Mengajukan Pertanyaan]
         ▼
┌─────────────────────────────────┐
│ Pencarian Semantik (Top-K Chunks│
└────────┬────────────────────────┘
         ▼
┌─────────────────────────────────┐
│ Susun RAG Prompt + Riwayat Chat │
└────────┬────────────────────────┘
         ▼
┌─────────────────────────────────┐
│ Google Gemini 2.0 Flash Engine  │
└────────┬────────────────────────┘
         ▼
┌─────────────────────────────────┐
│ Jawaban dengan Sitasi [Page X]  │
└─────────────────────────────────┘
```

---

## 🛠️ Teknologi & Stack

- **Backend Framework**: Python 3.12, **FastAPI 0.115**, Uvicorn.
- **Basis Data**: SQLite (Metadata & Riwayat) + **ChromaDB** (Vector Database).
- **Pemrosesan PDF**: PyMuPDF (`fitz`), ReportLab (Ekspor PDF).
- **Model Embedding**: Sentence-Transformers (`all-MiniLM-L6-v2`).
- **Mesin Kecerdasan Buatan (LLM)**: **Google Gemini 2.0 Flash** via SDK Google GenAI resmi.
- **Frontend SPA**: HTML5, TypeScript, Tailwind CSS (Glassmorphism UI).
- **DevOps & Testing**: Docker, Docker Compose, Nginx, Pytest, GitHub Actions CI/CD.

---

## 🚀 Quick Start

### Prasyarat
- **Python 3.11+** dan `pip`.
- **Google Gemini API Key** — [Dapatkan gratis di Google AI Studio](https://aistudio.google.com/).

### 1. Clone & Setup Lingkungan
```bash
git clone https://github.com/a1fariz/StudyMateAI.git
cd StudyMateAI

# Buat virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux

# Instal dependensi
pip install -r requirements.txt
```

### 2. Konfigurasi Lingkungan (`.env`)
```bash
copy .env.example .env         # Windows
# cp .env.example .env         # macOS / Linux
```

Edit file `.env` dan masukkan API key Anda:
```env
GEMINI_API_KEY=your-gemini-api-key-here
```

### 3. Jalankan Server Backend
```bash
uvicorn backend.main:app --reload --port 8001
```

### 4. Akses Aplikasi
- 🌐 **Web App**: `http://localhost:8001`
- 📚 **Interactive Swagger API Docs**: `http://localhost:8001/docs`
- 📖 **ReDoc Documentation**: `http://localhost:8001/redoc`

---

## 📡 Spesifikasi API

### Autentikasi
| Method | Endpoint | Deskripsi |
|---|---|---|
| `POST` | `/api/v1/auth/register` | Mendaftarkan pengguna baru |
| `POST` | `/api/v1/auth/login` | Login & mendapatkan JWT Bearer Token |
| `GET` | `/api/v1/auth/me` | Mengambil data profil pengguna aktif |

### Dokumen & Indeksasi AI
| Method | Endpoint | Deskripsi |
|---|---|---|
| `POST` | `/api/v1/documents/upload` | Mengunggah berkas PDF |
| `GET` | `/api/v1/documents/` | Daftar seluruh dokumen pengguna |
| `POST` | `/api/v1/documents/{id}/process` | Pipeline Chunking + Embedding + Indexing |
| `POST` | `/api/v1/search` | Pencarian semantik pada vektor teks |

### RAG Chat & Fitur Pembelajaran
| Method | Endpoint | Deskripsi |
|---|---|---|
| `POST` | `/api/v1/chat` | Tanya jawab RAG dengan sitasi halaman |
| `POST` | `/api/v1/documents/{id}/summary` | Pembuatan ringkasan 5 poin kunci |
| `POST` | `/api/v1/documents/{id}/quiz` | Generator kuis pilihan ganda |
| `POST` | `/api/v1/documents/{id}/flashcards` | Generator flashcard 3D |
| `POST` | `/api/v1/documents/{id}/study-plan` | Generator jadwal belajar bertarget |
| `GET` | `/api/v1/documents/{id}/export-summary` | Unduh ringkasan materi dalam format PDF |

---

## 🧪 Pengujian (Testing)

Jalankan rangkaian unit & integration test komprehensif menggunakan pytest:
```bash
python -m pytest tests/ -v
```

---

## 🐳 Deployment (Docker Compose)

```bash
# Build dan jalankan seluruh container
docker compose up --build -d

# Cek log sistem
docker compose logs -f
```

---

## 👨‍💻 Author

Dikembangkan oleh **Muhammad Hafiz Alfarizi** ([@a1fariz](https://github.com/a1fariz)).  
*Dibuat untuk merevolusi efisiensi belajar dengan teknologi Retrieval-Augmented Generation.*
