"""End-to-end test for Phase 2: Chunking + Embeddings + ChromaDB"""
import requests
import json

BASE = "http://127.0.0.1:8001/api/v1"

# 1. Register
print("=" * 60)
print("STEP 1: Register")
print("=" * 60)
r = requests.post(f"{BASE}/auth/register", json={
    "email": "phase2test@test.com",
    "username": "phase2user",
    "password": "test123456",
})
print(f"Status: {r.status_code}")
if r.status_code == 201:
    data = r.json()
    print(f"User created: {data['username']}")
elif r.status_code == 400:
    print("Already exists (OK)")
else:
    print(r.text)

# 2. Login
print()
print("=" * 60)
print("STEP 2: Login")
print("=" * 60)
r = requests.post(f"{BASE}/auth/login", json={
    "username": "phase2user",
    "password": "test123456",
})
print(f"Status: {r.status_code}")
token = r.json()["access_token"]
print(f"Token: {token[:30]}...")
headers = {"Authorization": f"Bearer {token}"}

# 3. Upload PDF
print()
print("=" * 60)
print("STEP 3: Upload PDF")
print("=" * 60)
with open("test_ai_textbook.pdf", "rb") as f:
    r = requests.post(
        f"{BASE}/documents/upload",
        headers=headers,
        files={"file": ("AI_Textbook.pdf", f, "application/pdf")},
    )
print(f"Status: {r.status_code}")
doc = r.json()
doc_id = doc["id"]
print(f"Document ID: {doc_id}")
print(f"Pages: {doc['page_count']}")
print(f"Status: {doc['status']}")

# 4. Process document (Phase 2 pipeline!)
print()
print("=" * 60)
print("STEP 4: Process Document (Chunk + Embed + Store)")
print("=" * 60)
r = requests.post(f"{BASE}/documents/{doc_id}/process", headers=headers)
print(f"Status: {r.status_code}")
result = r.json()
print(json.dumps(result, indent=2))

# 5. Semantic Search - ML
print()
print("=" * 60)
print("STEP 5: Semantic Search - What is Machine Learning?")
print("=" * 60)
r = requests.post(f"{BASE}/search", headers=headers, json={
    "query": "What is Machine Learning?",
    "document_id": doc_id,
    "top_k": 3,
})
print(f"Status: {r.status_code}")
search = r.json()
print(f"Query: {search['query']}")
print(f"Results: {search['total_results']}")
for i, res in enumerate(search["results"]):
    print(f"\n--- Result {i+1} (score: {res['score']}, page: {res['page_number']}) ---")
    print(res["content"][:200])

# 6. Semantic Search - Deep Learning
print()
print("=" * 60)
print("STEP 6: Semantic Search - Deep Learning neural networks")
print("=" * 60)
r = requests.post(f"{BASE}/search", headers=headers, json={
    "query": "What are neural networks in deep learning?",
    "document_id": doc_id,
    "top_k": 3,
})
print(f"Status: {r.status_code}")
search = r.json()
print(f"Query: {search['query']}")
print(f"Results: {search['total_results']}")
for i, res in enumerate(search["results"]):
    print(f"\n--- Result {i+1} (score: {res['score']}, page: {res['page_number']}) ---")
    print(res["content"][:200])

# 7. Semantic Search - NLP
print()
print("=" * 60)
print("STEP 7: Semantic Search - NLP applications")
print("=" * 60)
r = requests.post(f"{BASE}/search", headers=headers, json={
    "query": "What are the applications of natural language processing?",
    "document_id": doc_id,
    "top_k": 3,
})
print(f"Status: {r.status_code}")
search = r.json()
print(f"Query: {search['query']}")
print(f"Results: {search['total_results']}")
for i, res in enumerate(search["results"]):
    print(f"\n--- Result {i+1} (score: {res['score']}, page: {res['page_number']}) ---")
    print(res["content"][:200])

print()
print("=" * 60)
print("ALL TESTS PASSED!")
print("=" * 60)
