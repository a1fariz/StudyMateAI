# 🎓 StudyMate AI — Architecture Document

> **Version**: 1.0.0  
> **Stack**: FastAPI · ChromaDB · Sentence-Transformers · Google Gemini  
> **Pattern**: Retrieval-Augmented Generation (RAG)

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (SPA)                           │
│              index.html + app.js (TailwindCSS)                  │
│   ┌─────────┬────────────┬──────────┬────────────┬───────────┐  │
│   │  Chat   │ Summarizer │   Quiz   │ Flashcards │   Plan    │  │
│   └────┬────┴─────┬──────┴────┬─────┴─────┬──────┴────┬──────┘  │
└────────┼──────────┼───────────┼───────────┼───────────┼─────────┘
         │          │           │           │           │
         │       REST API (JSON over HTTP)              │
         │          │           │           │           │
┌────────┼──────────┼───────────┼───────────┼───────────┼─────────┐
│        ▼          ▼           ▼           ▼           ▼         │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │              FastAPI Application (main.py)               │   │
│   │                                                         │   │
│   │   ┌────────┐ ┌───────────┐ ┌────────┐ ┌──────────────┐ │   │
│   │   │  Auth  │ │ Documents │ │ Search │ │ Chat (RAG)   │ │   │
│   │   │ Router │ │  Router   │ │ Router │ │   Router     │ │   │
│   │   └───┬────┘ └─────┬─────┘ └───┬────┘ └──────┬───────┘ │   │
│   │       │             │           │              │         │   │
│   │   ┌───▼─────────────▼───────────▼──────────────▼───────┐ │   │
│   │   │              Service Layer                          │ │   │
│   │   │  auth · pdf_processor · chunking · embedding       │ │   │
│   │   │  vector_store · gemini_service · rag_service        │ │   │
│   │   │  generator_service · pdf_exporter                   │ │   │
│   │   └──────┬────────────┬──────────────┬─────────────────┘ │   │
│   └──────────┼────────────┼──────────────┼───────────────────┘   │
│              │            │              │                        │
│   ┌──────────▼────┐ ┌─────▼──────┐ ┌────▼─────────────────────┐  │
│   │   SQLite DB   │ │  ChromaDB  │ │  Google Gemini API       │  │
│   │  (aiosqlite)  │ │  (Vectors) │ │  (gemini-2.0-flash)     │  │
│   │               │ │            │ │                          │  │
│   │  Users        │ │  Document  │ │  RAG Answers             │  │
│   │  Documents    │ │  Chunks +  │ │  Summaries / Quizzes     │  │
│   │  Conversations│ │  Embeddings│ │  Flashcards / Plans      │  │
│   │  Messages     │ │            │ │                          │  │
│   └───────────────┘ └────────────┘ └──────────────────────────┘  │
│                       Backend Server                             │
└──────────────────────────────────────────────────────────────────┘
```

---

## RAG Pipeline Flow

```
User Question
      │
      ▼
┌─────────────┐     ┌──────────────┐     ┌────────────────┐
│ Embed Query │────▶│ Search       │────▶│ Retrieve Top-K │
│ (MiniLM)    │     │ ChromaDB     │     │ Chunks         │
└─────────────┘     └──────────────┘     └───────┬────────┘
                                                  │
                    ┌──────────────┐               │
                    │ Load Chat    │◀──────────────┘
                    │ History      │
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │ Build RAG    │
                    │ Prompt       │
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │ Gemini API   │
                    │ Generate     │
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │ Extract      │
                    │ Citations    │
                    └──────┬───────┘
                           │
                           ▼
                    Save to DB +
                    Return Answer
```

---

## Database Schema

### Users Table
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | Primary Key |
| email | String | Unique, Not Null |
| username | String | Unique, Not Null |
| hashed_password | String | Not Null |
| is_active | Boolean | Default True |
| created_at | DateTime | Auto |
| updated_at | DateTime | Auto |

### Documents Table
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | Primary Key |
| filename | String | Not Null |
| original_filename | String | Not Null |
| file_path | String | Not Null |
| file_size | Integer | Not Null |
| page_count | Integer | Default 0 |
| status | String | uploaded/processing/processed/failed |
| error_message | String | Nullable |
| owner_id | UUID | FK → users |
| uploaded_at | DateTime | Auto |

### Conversations Table
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | Primary Key |
| title | String | Not Null |
| user_id | UUID | FK → users |
| document_id | UUID | FK → documents, Nullable |
| created_at | DateTime | Auto |
| updated_at | DateTime | Auto |

### Messages Table
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | Primary Key |
| role | String | user/assistant |
| content | Text | Not Null |
| sources | Text (JSON) | Nullable |
| conversation_id | UUID | FK → conversations |
| created_at | DateTime | Auto |

---

## Complete API Reference

### 🔐 Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register new user |
| POST | `/api/v1/auth/login` | Login & get JWT token |
| GET | `/api/v1/auth/me` | Get current user profile |

### 📄 Documents
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/documents/upload` | Upload PDF document |
| GET | `/api/v1/documents/` | List user's documents |
| GET | `/api/v1/documents/{id}` | Get document details |
| POST | `/api/v1/documents/{id}/parse` | Extract text from PDF |
| DELETE | `/api/v1/documents/{id}` | Delete document + vectors |

### 🔍 AI Search
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/documents/{id}/process` | Full AI pipeline (chunk → embed → store) |
| POST | `/api/v1/search` | Semantic similarity search |

### 💬 Chat (RAG)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/chat` | Ask question → RAG answer with citations |
| GET | `/api/v1/conversations` | List conversations |
| GET | `/api/v1/conversations/{id}` | Get conversation with messages |
| DELETE | `/api/v1/conversations/{id}` | Delete conversation |

### 🧠 Smart Study Features
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/documents/{id}/summary` | Generate AI summary |
| POST | `/api/v1/documents/{id}/quiz` | Generate practice quiz (MCQ) |
| POST | `/api/v1/documents/{id}/flashcards` | Generate study flashcards |
| POST | `/api/v1/documents/{id}/study-plan` | Generate study schedule |
| GET | `/api/v1/documents/{id}/export-summary` | Download summary as PDF |

### ⚙️ System
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check (Docker/LB) |
| GET | `/docs` | Swagger UI |
| GET | `/redoc` | ReDoc documentation |

---

## Security Measures

| Feature | Implementation |
|---------|---------------|
| Authentication | JWT Bearer tokens (python-jose) |
| Password Storage | bcrypt hashing |
| Rate Limiting | In-memory token bucket (60 req/min) |
| CORS | Configurable origins via `.env` |
| Security Headers | X-Content-Type-Options, X-Frame-Options, Referrer-Policy |
| Input Validation | Pydantic schemas on all endpoints |
| File Validation | PDF-only uploads, size limits enforced |
| Data Isolation | Documents & conversations scoped to user ownership |
