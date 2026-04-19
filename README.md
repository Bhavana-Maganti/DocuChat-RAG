# Project 1 — DocuChat: RAG Chatbot over your PDFs

A full-stack Retrieval-Augmented Generation app. Upload PDFs, ask questions in natural language, get answers with source citations.

## Tech stack

- **Backend:** FastAPI, LangChain, ChromaDB (vector DB), OpenAI / Groq / Ollama
- **Frontend:** React (Vite) + Tailwind
- **Embeddings:** `sentence-transformers/all-MiniLM-L6-v2` (free, runs locally)

## Architecture

```
 PDF upload ──► chunker ──► embedder ──► ChromaDB
                                              │
 User question ──► embedder ──► similarity search
                                              │
                                              ▼
                                  top-k chunks + question
                                              │
                                              ▼
                                         LLM (LangChain)
                                              │
                                              ▼
                                   Answer + source citations
```

## Quickstart (backend)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # on Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # then edit with your LLM API key
uvicorn main:app --reload
```

Open http://localhost:8000/docs for Swagger UI.

## Quickstart (frontend)

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173.

## API

- `POST /upload` — multipart PDF upload, indexes it into ChromaDB
- `POST /ask` — body `{question: str}`, returns `{answer, sources}`
- `GET /health` — health check

## What I learned

- **Vector stores don't deduplicate by default.** While testing, I
  uploaded the same PDF twice and ChromaDB stored every chunk twice,
  so retrieval returned identical snippets. A production fix is to
  hash each chunk and upsert with a stable ID like
  (source_file, chunk_index).

- **Retrieval and generation are separate problems.** Testing that the
  vector search returned the right chunks BEFORE worrying about the
  LLM's answer helped me isolate bugs. Good retrieval almost
  guarantees a good answer; bad retrieval guarantees a bad one,
  no matter how good the LLM is.

- **Chunk size and overlap directly affect answer quality.** With
  chunk_size = 800 and overlap = 120, I avoided cutting important
  sentences across chunk boundaries. Smaller chunks lose context;
  larger ones dilute relevance.

- **Provider-agnostic LLM access is worth the tiny upfront cost.**
  Wiring the backend to switch between OpenAI and Groq via a single
  env variable let me build the whole project at zero cost using
  Groq's free tier, while keeping the door open to swap providers
  for production.

## Next steps

- Add user auth + per-user document isolation
- Swap ChromaDB for Pinecone/Weaviate for cloud scale
- Add reranking (Cohere or BGE) for better retrieval
