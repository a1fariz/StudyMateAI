<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi&logoColor=white"/>
  <img src="https://img.shields.io/badge/Gemini_2.0-Flash-4285F4?style=for-the-badge&logo=google&logoColor=white"/>
  <img src="https://img.shields.io/badge/ChromaDB-Vector_Store-FF6F00?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge"/>
</p>

<h1 align="center">🎓 StudyMate AI</h1>

<p align="center">
  <strong>An intelligent study assistant powered by Retrieval-Augmented Generation (RAG)</strong><br/>
  Upload textbooks → Ask questions with citations → Generate quizzes, flashcards & study plans
</p>

<p align="center">
  <a href="#-features">Features</a> •
  <a href="#-tech-stack">Tech Stack</a> •
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-api-reference">API</a> •
  <a href="#-architecture">Architecture</a> •
  <a href="#-testing">Testing</a> •
  <a href="#-deployment">Deployment</a>
</p>

---

## ✨ Features

| Feature | Description | Status |
|---------|-------------|--------|
| 🔐 **JWT Authentication** | Secure register/login with bcrypt + JWT tokens | ✅ |
| 📄 **PDF Upload & Parsing** | Upload PDFs, extract text with PyMuPDF | ✅ |
| 🧠 **AI Processing Pipeline** | Chunk → Embed → Store in vector database | ✅ |
| 🔍 **Semantic Search** | Natural language search across documents | ✅ |
| 💬 **RAG Chat Assistant** | AI Q&A with source page citations | ✅ |
| 📝 **Auto Summary Generator** | 5-point AI summaries with PDF export | ✅ |
| ❓ **Quiz Generator** | AI-generated MCQ practice exams with scoring | ✅ |
| 🃏 **Flashcard Generator** | Interactive 3D flip flashcards | ✅ |
| 📅 **Study Plan Generator** | Day-by-day study schedules | ✅ |
| 🛡️ **Rate Limiting & Security** | Token-bucket rate limiter + security headers | ✅ |
| 🐳 **Docker Ready** | Full Docker Compose deployment | ✅ |
| 🧪 **CI/CD Pipeline** | GitHub Actions: lint, test, build, audit | ✅ |

---

## 🏗️ Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Backend** | FastAPI + Uvicorn | Async REST API framework |
| **Frontend** | HTML + TailwindCSS + Vanilla JS | Single-page application |
| **Database** | SQLite (aiosqlite) | User, document & conversation storage |
| **Vector Store** | ChromaDB | Semantic search index |
| **Embeddings** | sentence-transformers (all-MiniLM-L6-v2) | Text → vector conversion |
| **LLM** | Google Gemini 2.0 Flash | RAG answers + content generation |
| **PDF Processing** | PyMuPDF | Text extraction from PDFs |
| **Auth** | python-jose + bcrypt | JWT tokens + password hashing |
| **PDF Export** | ReportLab | Summary report generation |
| **Deployment** | Docker + Nginx | Containerized production setup |
| **CI/CD** | GitHub Actions | Automated testing & builds |

---

## 📁 Project Structure

```
StudyMate-AI/
│
├── backend/
│   ├── main.py                    # FastAPI app + middleware
│   ├── config.py                  # Settings + validation
│   ├── database.py                # Async SQLAlchemy engine
│   ├── Dockerfile                 # Backend container
│   │
│   ├── models/                    # ORM models
│   │   ├── user.py                # User entity
│   │   ├── document.py            # Document entity
│   │   └── conversation.py        # Conversation + Message entities
│   │
│   ├── schemas/                   # Pydantic request/response schemas
│   │   ├── auth.py                # Auth schemas
│   │   ├── document.py            # Document schemas
│   │   ├── chat.py                # Chat + conversation schemas
│   │   ├── search.py              # Search schemas
│   │   └── features.py            # Generator feature schemas
│   │
│   ├── routers/                   # API endpoint handlers
│   │   ├── auth.py                # /auth/* endpoints
│   │   ├── documents.py           # /documents/* CRUD
│   │   ├── search.py              # /documents/{id}/process + /search
│   │   ├── chat.py                # /chat + /conversations/*
│   │   └── features.py            # Summary, quiz, flashcard, plan
│   │
│   └── services/                  # Business logic layer
│       ├── auth.py                # Password hashing + JWT
│       ├── pdf_processor.py       # PyMuPDF text extraction
│       ├── chunking.py            # Text segmentation
│       ├── embedding.py           # Sentence-transformer embeddings
│       ├── vector_store.py        # ChromaDB CRUD operations
│       ├── gemini_service.py      # Gemini API wrapper
│       ├── rag_service.py         # Full RAG pipeline orchestrator
│       ├── generator_service.py   # Summary/quiz/flashcard/plan gen
│       └── pdf_exporter.py        # ReportLab PDF builder
│
├── frontend/
│   ├── index.html                 # SPA with 5 workspace tabs
│   ├── app.js                     # All frontend logic
│   └── Dockerfile                 # Nginx-based frontend container
│
├── tests/
│   └── test_app.py                # Comprehensive test suite
│
├── docs/
│   └── architecture.md            # System architecture & API reference
│
├── .github/workflows/
│   └── ci.yml                     # GitHub Actions CI/CD pipeline
│
├── docker-compose.yml             # Full stack deployment
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment template (all settings)
├── .gitignore                     # Git exclusions
└── README.md                      # ← You are here
```

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+** with `pip`
- **Google Gemini API key** — [Get one free →](https://aistudio.google.com/apikey)

### 1. Clone & Setup

```bash
git clone https://github.com/a1fariz/StudyMateAI.git
cd StudyMateAI

# Create virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
copy .env.example .env         # Windows
# cp .env.example .env         # macOS/Linux
```

Edit `.env` and set your Gemini API key:
```
GEMINI_API_KEY=your-gemini-api-key-here
```

### 3. Run the Server

```bash
uvicorn backend.main:app --reload --port 8001
```

### 4. Open the App

| URL | What |
|-----|------|
| [http://localhost:8001](http://localhost:8001) | 🎓 StudyMate AI Frontend |
| [http://localhost:8001/docs](http://localhost:8001/docs) | 📡 Swagger API Docs |
| [http://localhost:8001/redoc](http://localhost:8001/redoc) | 📖 ReDoc API Docs |
| [http://localhost:8001/health](http://localhost:8001/health) | ❤️ Health Check |

---

## 📡 API Reference

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/auth/register` | Register new user |
| `POST` | `/api/v1/auth/login` | Login → JWT token |
| `GET` | `/api/v1/auth/me` | Current user profile |

### Documents
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/documents/upload` | Upload PDF |
| `GET` | `/api/v1/documents/` | List documents |
| `GET` | `/api/v1/documents/{id}` | Document details |
| `POST` | `/api/v1/documents/{id}/parse` | Extract text |
| `DELETE` | `/api/v1/documents/{id}` | Delete document |

### AI Search
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/documents/{id}/process` | Chunk + Embed + Index |
| `POST` | `/api/v1/search` | Semantic search |

### Chat (RAG)
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/chat` | Ask → RAG answer |
| `GET` | `/api/v1/conversations` | List conversations |
| `GET` | `/api/v1/conversations/{id}` | Conversation detail |
| `DELETE` | `/api/v1/conversations/{id}` | Delete conversation |

### Smart Features
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/documents/{id}/summary` | AI summary |
| `POST` | `/api/v1/documents/{id}/quiz?num_questions=10` | Practice quiz |
| `POST` | `/api/v1/documents/{id}/flashcards` | Flashcards |
| `POST` | `/api/v1/documents/{id}/study-plan?days=7` | Study schedule |
| `GET` | `/api/v1/documents/{id}/export-summary` | Download PDF |

---

## 🏛️ Architecture

StudyMate AI uses a **Retrieval-Augmented Generation (RAG)** architecture:

```
📄 PDF Upload
      ↓
🔪 Text Chunking (RecursiveCharacterTextSplitter)
      ↓
🧮 Embedding Generation (all-MiniLM-L6-v2)
      ↓
💾 Vector Storage (ChromaDB)
      ↓
❓ User asks a question
      ↓
🔍 Semantic Search → Top-K relevant chunks
      ↓
📜 Build RAG Prompt (chunks + history + system instructions)
      ↓
🤖 Gemini 2.0 Flash generates answer with [Page X] citations
      ↓
💬 Response with sources returned to user
```

> See [docs/architecture.md](docs/architecture.md) for the complete system diagram, database schema, and full API reference.

---

## 🧪 Testing

### Install Test Dependencies

```bash
pip install pytest pytest-asyncio httpx
```

### Run Tests

```bash
python -m pytest tests/ -v
```

### Test Coverage

| Area | Tests |
|------|-------|
| Configuration | Settings loading, validation, defaults |
| Authentication | Password hashing, JWT tokens, login/register endpoints |
| PDF Processing | Text extraction, page counting |
| Chunking | Text splitting, page preservation |
| Embeddings | Query embedding, batch embedding, consistency |
| Rate Limiter | Within limit, over limit, IP isolation |
| API Endpoints | Health, auth, documents, search, chat |

---

## 🐳 Deployment

### Docker Compose (Recommended)

```bash
# Build and start all services
docker compose up --build -d

# Check health
curl http://localhost:8001/health

# View logs
docker compose logs -f
```

| Service | URL | Description |
|---------|-----|-------------|
| Backend | `http://localhost:8001` | FastAPI + API |
i| Frontend | `http://localhost:80` | Nginx SPA (proxies `/api/` to backend) |

The frontend container’s nginx config forwards `/api/*` to the backend service, so the SPA can use same-origin API calls when opened at `http://localhost`. For local development without Docker, run uvicorn on port **8001** — FastAPI serves the SPA and API together.

### Manual Deployment

```bash
# Production mode
uvicorn backend.main:app --host 0.0.0.0 --port 8001 --workers 4
```

---

## 🔒 Security

| Feature | Detail |
|---------|--------|
| **Authentication** | JWT Bearer tokens with configurable expiry |
| **Passwords** | bcrypt hashing with salt |
| **Rate Limiting** | 60 requests/minute per IP (configurable) |
| **CORS** | Configurable allowed origins |
| **Security Headers** | X-Content-Type-Options, X-Frame-Options, Referrer-Policy |
| **Input Validation** | Pydantic schemas on every endpoint |
| **File Validation** | PDF-only, size limit enforced |
| **Data Isolation** | Multi-user with per-user document/conversation scoping |

---

## 🗺️ Development Phases

| Phase | Scope | Status |
|-------|-------|--------|
| **Phase 1** | Auth + PDF Upload + Text Extraction | ✅ Complete |
| **Phase 2** | Chunking + Embeddings + ChromaDB | ✅ Complete |
| **Phase 3** | Gemini Integration + RAG Chat + History | ✅ Complete |
| **Phase 4** | Summary, Quiz, Flashcard, Study Plan | ✅ Complete |
| **Phase 5** | Docker, Tests, CI/CD, Security, Polish | ✅ Complete |

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 👤 Author

Built as a portfolio project demonstrating:

- ⚡ **Python Backend Development** — FastAPI, async SQLAlchemy, service-layer architecture
- 🔗 **REST API Design** — RESTful endpoints, Pydantic validation, OpenAPI docs
- 🗄️ **Database Design** — Relational (SQLite) + Vector (ChromaDB) dual-store
- 🤖 **RAG Architecture** — Retrieval-Augmented Generation pipeline
- 🧠 **LLM Integration** — Google Gemini 2.0 Flash with structured output
- 🎨 **Frontend Development** — Modern SPA with TailwindCSS glassmorphism
- 🐳 **DevOps** — Docker, CI/CD, rate limiting, security hardening
- 🧪 **Testing** — pytest + pytest-asyncio comprehensive test suite

## Verification scope

See the Testing section for reproducible checks and GitHub Actions for individual run results. Generated answers and study materials may contain mistakes; page citations help readers inspect the original document. A configured pipeline does not by itself establish deployment availability or answer accuracy.

---

[Portfolio Alfa Rizi](https://alfarizi.my.id) · [GitHub profile](https://github.com/a1fariz) · [Contact](mailto:alfarizi.developer@gmail.com)
