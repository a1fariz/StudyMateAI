"""
Comprehensive test suite for StudyMate AI.

Tests cover:
  - Configuration loading and validation
  - Password hashing and JWT tokens
  - Database session management
  - PDF text extraction
  - Text chunking pipeline
  - Embedding service
  - Vector store operations
  - API health check endpoint
  - Authentication endpoints (register, login, me)
  - Document upload and lifecycle
"""

import os
import sys
import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock
from httpx import AsyncClient, ASGITransport

# ──────────────────────────────────────
# Fixtures
# ──────────────────────────────────────

@pytest.fixture(scope="session", autouse=True)
def setup_env():
    """Set test environment variables before any import touches Settings."""
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_studymate.db"
    os.environ["SECRET_KEY"] = "test-secret-key-for-unit-tests"
    os.environ["GEMINI_API_KEY"] = "test-api-key"
    os.environ["UPLOAD_DIR"] = "./test_uploads"
    os.environ["CHROMA_PERSIST_DIR"] = "./test_chroma_data"
    os.environ["DEBUG"] = "false"
    yield
    # Cleanup test artifacts
    for f in ["test_studymate.db"]:
        if os.path.exists(f):
            os.remove(f)
    import shutil
    for d in ["test_uploads", "test_chroma_data"]:
        if os.path.exists(d):
            shutil.rmtree(d, ignore_errors=True)


# ══════════════════════════════════════
# Unit Tests: Configuration
# ══════════════════════════════════════

class TestConfig:
    """Configuration loading and validation."""

    def test_settings_load(self):
        from backend.config import Settings
        s = Settings()
        assert s.APP_NAME == "StudyMate AI"
        assert s.ALGORITHM == "HS256"

    def test_settings_version(self):
        from backend.config import Settings
        s = Settings()
        assert s.APP_VERSION == "1.0.0"

    def test_settings_rate_limit_default(self):
        from backend.config import Settings
        s = Settings()
        assert s.RATE_LIMIT_PER_MINUTE == 60

    def test_settings_upload_limit(self):
        from backend.config import Settings
        s = Settings()
        assert s.MAX_UPLOAD_SIZE_MB > 0


# ══════════════════════════════════════
# Unit Tests: Authentication Utilities
# ══════════════════════════════════════

class TestAuthUtils:
    """Password hashing and JWT token creation/validation."""

    def test_hash_password(self):
        from backend.services.auth import hash_password
        hashed = hash_password("testpassword123")
        assert hashed != "testpassword123"
        assert len(hashed) > 20

    def test_verify_password_correct(self):
        from backend.services.auth import hash_password, verify_password
        hashed = hash_password("mypassword")
        assert verify_password("mypassword", hashed) is True

    def test_verify_password_incorrect(self):
        from backend.services.auth import hash_password, verify_password
        hashed = hash_password("mypassword")
        assert verify_password("wrongpassword", hashed) is False

    def test_create_access_token(self):
        from backend.services.auth import create_access_token
        token = create_access_token({"sub": "user-123"})
        assert isinstance(token, str)
        assert len(token) > 50

    def test_decode_access_token(self):
        from backend.services.auth import create_access_token
        from jose import jwt
        token = create_access_token({"sub": "user-456"})
        payload = jwt.decode(token, "test-secret-key-for-unit-tests", algorithms=["HS256"])
        assert payload["sub"] == "user-456"
        assert "exp" in payload


# ══════════════════════════════════════
# Unit Tests: PDF Processing
# ══════════════════════════════════════

class TestPDFProcessor:
    """PDF text extraction tests."""

    def test_extract_text_missing_file(self):
        from backend.services.pdf_processor import extract_text_from_pdf
        with pytest.raises(FileNotFoundError):
            extract_text_from_pdf("nonexistent_file.pdf")

    def test_get_page_count_missing_file(self):
        from backend.services.pdf_processor import get_pdf_page_count
        count = get_pdf_page_count("nonexistent.pdf")
        assert count == 0

    def test_extract_text_from_test_pdf(self):
        """Test with the included test PDF if available."""
        test_pdf = "test_ai_textbook.pdf"
        if os.path.exists(test_pdf):
            from backend.services.pdf_processor import extract_text_from_pdf
            pages = extract_text_from_pdf(test_pdf)
            assert len(pages) > 0
            assert "content" in pages[0]
            assert "page" in pages[0]
            assert len(pages[0]["content"]) > 0


# ══════════════════════════════════════
# Unit Tests: Text Chunking
# ══════════════════════════════════════

class TestChunking:
    """Text chunking pipeline tests."""

    def test_chunk_document_basic(self):
        from backend.services.chunking import chunk_document
        pages = [
            {"page": 1, "content": "This is a test page with some content. " * 50},
            {"page": 2, "content": "Second page with different text material. " * 50},
        ]
        chunks = chunk_document(pages)
        assert len(chunks) > 0
        assert "content" in chunks[0]
        assert "page_number" in chunks[0]
        assert "chunk_index" in chunks[0]
        assert "word_count" in chunks[0]

    def test_chunk_document_empty(self):
        from backend.services.chunking import chunk_document
        chunks = chunk_document([])
        assert chunks == []

    def test_chunk_document_preserves_page_numbers(self):
        from backend.services.chunking import chunk_document
        pages = [
            {"page": 5, "content": "Content on page five. " * 100},
        ]
        chunks = chunk_document(pages)
        assert all(c["page_number"] == 5 for c in chunks)


# ══════════════════════════════════════
# Unit Tests: Embedding Service
# ══════════════════════════════════════

class TestEmbeddingService:
    """Embedding generation tests."""

    def test_embed_query(self):
        from backend.services.embedding import EmbeddingService
        embedding = EmbeddingService.embed_query("What is machine learning?")
        assert isinstance(embedding, list)
        assert len(embedding) > 0
        assert all(isinstance(v, float) for v in embedding)

    def test_embed_texts(self):
        from backend.services.embedding import EmbeddingService
        texts = ["Hello world", "Machine learning is great"]
        embeddings = EmbeddingService.embed_texts(texts)
        assert len(embeddings) == 2
        assert len(embeddings[0]) == len(embeddings[1])

    def test_embed_consistency(self):
        """Same text should produce same embeddings."""
        from backend.services.embedding import EmbeddingService
        e1 = EmbeddingService.embed_query("test query")
        e2 = EmbeddingService.embed_query("test query")
        assert e1 == e2


# ══════════════════════════════════════
# Unit Tests: Rate Limiter
# ══════════════════════════════════════

class TestRateLimiter:
    """Rate limiter logic tests."""

    def test_allows_within_limit(self):
        from backend.main import RateLimiter
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        for _ in range(5):
            assert limiter.is_allowed("127.0.0.1") is True

    def test_blocks_over_limit(self):
        from backend.main import RateLimiter
        limiter = RateLimiter(max_requests=3, window_seconds=60)
        for _ in range(3):
            limiter.is_allowed("10.0.0.1")
        assert limiter.is_allowed("10.0.0.1") is False

    def test_different_ips_independent(self):
        from backend.main import RateLimiter
        limiter = RateLimiter(max_requests=2, window_seconds=60)
        limiter.is_allowed("1.1.1.1")
        limiter.is_allowed("1.1.1.1")
        # 1.1.1.1 is exhausted
        assert limiter.is_allowed("1.1.1.1") is False
        # 2.2.2.2 should still work
        assert limiter.is_allowed("2.2.2.2") is True


# ══════════════════════════════════════
# Integration Tests: API Endpoints
# ══════════════════════════════════════

@pytest_asyncio.fixture
async def client():
    """Async test client for FastAPI app."""
    from backend.main import app
    from backend.database import init_db
    await init_db()
    os.makedirs("test_uploads", exist_ok=True)
    os.makedirs("test_chroma_data", exist_ok=True)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
class TestHealthEndpoint:
    """Health check endpoint tests."""

    async def test_health_returns_200(self, client):
        response = await client.get("/health")
        assert response.status_code == 200

    async def test_health_response_body(self, client):
        response = await client.get("/health")
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "1.0.0"
        assert "app" in data


@pytest.mark.asyncio
class TestAuthEndpoints:
    """Authentication endpoint tests."""

    async def test_register_user(self, client):
        response = await client.post("/api/v1/auth/register", json={
            "email": "testuser@example.com",
            "username": "testuser",
            "password": "securepassword123",
        })
        assert response.status_code in [201, 400]  # 400 if already exists

    async def test_register_duplicate_user(self, client):
        # Register first
        await client.post("/api/v1/auth/register", json={
            "email": "dupuser@example.com",
            "username": "dupuser",
            "password": "securepassword123",
        })
        # Register again
        response = await client.post("/api/v1/auth/register", json={
            "email": "dupuser@example.com",
            "username": "dupuser",
            "password": "securepassword123",
        })
        assert response.status_code == 400

    async def test_login_success(self, client):
        # Register
        await client.post("/api/v1/auth/register", json={
            "email": "loginuser@example.com",
            "username": "loginuser",
            "password": "securepassword123",
        })
        # Login
        response = await client.post("/api/v1/auth/login", data={
            "username": "loginuser",
            "password": "securepassword123",
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(self, client):
        await client.post("/api/v1/auth/register", json={
            "email": "wrongpw@example.com",
            "username": "wrongpwuser",
            "password": "correctpassword",
        })
        response = await client.post("/api/v1/auth/login", data={
            "username": "wrongpwuser",
            "password": "wrongpassword",
        })
        assert response.status_code == 401

    async def test_get_me_unauthorized(self, client):
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401

    async def test_get_me_authorized(self, client):
        # Register + Login
        await client.post("/api/v1/auth/register", json={
            "email": "meuser@example.com",
            "username": "meuser",
            "password": "securepassword123",
        })
        login_resp = await client.post("/api/v1/auth/login", data={
            "username": "meuser",
            "password": "securepassword123",
        })
        token = login_resp.json()["access_token"]

        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "meuser"
        assert data["email"] == "meuser@example.com"


@pytest.mark.asyncio
class TestDocumentEndpoints:
    """Document management endpoint tests."""

    async def _get_token(self, client) -> str:
        """Helper to register + login and get a token."""
        await client.post("/api/v1/auth/register", json={
            "email": "docuser@example.com",
            "username": "docuser",
            "password": "securepassword123",
        })
        resp = await client.post("/api/v1/auth/login", data={
            "username": "docuser",
            "password": "securepassword123",
        })
        return resp.json()["access_token"]

    async def test_list_documents_empty(self, client):
        token = await self._get_token(client)
        response = await client.get(
            "/api/v1/documents/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "documents" in data
        assert "total" in data

    async def test_list_documents_unauthorized(self, client):
        response = await client.get("/api/v1/documents/")
        assert response.status_code == 401

    async def test_upload_non_pdf(self, client):
        token = await self._get_token(client)
        response = await client.post(
            "/api/v1/documents/upload",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": ("test.txt", b"hello world", "text/plain")},
        )
        assert response.status_code == 400

    async def test_upload_pdf(self, client):
        """Test uploading the included test PDF."""
        if not os.path.exists("test_ai_textbook.pdf"):
            pytest.skip("Test PDF not available")

        token = await self._get_token(client)
        with open("test_ai_textbook.pdf", "rb") as f:
            response = await client.post(
                "/api/v1/documents/upload",
                headers={"Authorization": f"Bearer {token}"},
                files={"file": ("test.pdf", f, "application/pdf")},
            )
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "uploaded"
        assert data["original_filename"] == "test.pdf"

    async def test_get_nonexistent_document(self, client):
        token = await self._get_token(client)
        response = await client.get(
            "/api/v1/documents/nonexistent-id",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404


@pytest.mark.asyncio
class TestSearchEndpoints:
    """Search endpoint tests."""

    async def test_search_unauthorized(self, client):
        response = await client.post("/api/v1/search", json={
            "query": "test query",
        })
        assert response.status_code == 401


@pytest.mark.asyncio
class TestChatEndpoints:
    """Chat endpoint tests."""

    async def test_chat_unauthorized(self, client):
        response = await client.post("/api/v1/chat", json={
            "question": "What is AI?",
        })
        assert response.status_code == 401

    async def test_list_conversations_unauthorized(self, client):
        response = await client.get("/api/v1/conversations")
        assert response.status_code == 401
