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

## What I learned (fill this in as you build — interviewers ask!)

- Why chunk size and overlap matter for retrieval quality
- Cosine similarity vs. MMR retrieval strategies
- Handling citations so users trust the answer
- Streaming LLM tokens for better UX

## Next steps

- Add user auth + per-user document isolation
- Swap ChromaDB for Pinecone/Weaviate for cloud scale
- Add reranking (Cohere or BGE) for better retrieval
