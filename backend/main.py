"""
DocuChat: RAG Chatbot backend.

Flow:
1. /upload   -> save PDF, split into chunks, embed, store in ChromaDB
2. /ask      -> embed question, retrieve top-k chunks, call LLM with context
3. /health   -> quick liveness check
"""
import os
import shutil
import uuid
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# LangChain + Chroma + embeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.prompts import PromptTemplate
from langchain.schema import Document

load_dotenv()

# ---------- Config ----------
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()
CHROMA_DIR = os.getenv("CHROMA_DIR", "./chroma_store")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "800"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "120"))
TOP_K = int(os.getenv("TOP_K", "4"))
UPLOAD_DIR = Path("./uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# ---------- LLM factory ----------
def get_llm():
    """Return a LangChain LLM based on the configured provider."""
    if LLM_PROVIDER == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=0.2,
        )
    elif LLM_PROVIDER == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(
            model=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
            temperature=0.2,
        )
    else:
        raise RuntimeError(f"Unknown LLM_PROVIDER: {LLM_PROVIDER}")

# Embeddings run locally, free, no API key needed.
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# Persistent Chroma collection
vectorstore = Chroma(
    collection_name="docuchat",
    embedding_function=embeddings,
    persist_directory=CHROMA_DIR,
)

# ---------- FastAPI ----------
app = FastAPI(title="DocuChat API", version="0.1.0")

# Allow the React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AskRequest(BaseModel):
    question: str


class Source(BaseModel):
    source: str
    page: int | None = None
    snippet: str


class AskResponse(BaseModel):
    answer: str
    sources: List[Source]


@app.get("/health")
def health():
    return {"status": "ok", "provider": LLM_PROVIDER}


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    """Accept a PDF, chunk + embed it, store in Chroma."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are supported.")

    # Save to disk
    file_id = uuid.uuid4().hex[:8]
    saved_path = UPLOAD_DIR / f"{file_id}_{file.filename}"
    with saved_path.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    # Load + split
    loader = PyPDFLoader(str(saved_path))
    raw_docs = loader.load()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks: List[Document] = splitter.split_documents(raw_docs)

    # Tag every chunk with filename for citations
    for c in chunks:
        c.metadata["source"] = file.filename

    vectorstore.add_documents(chunks)
    # Chroma persists automatically when persist_directory is set.

    return {"file": file.filename, "chunks_indexed": len(chunks)}


# Prompt template: tells the LLM to ONLY use the retrieved context.
PROMPT = PromptTemplate.from_template(
    """You are a helpful assistant answering questions about a user's documents.
Use ONLY the context below to answer. If the answer isn't in the context, say
"I don't have enough information in the provided documents."

Context:
{context}

Question: {question}

Answer (be concise, cite page numbers when visible):"""
)


@app.post("/ask", response_model=AskResponse)
def ask(body: AskRequest):
    if not body.question.strip():
        raise HTTPException(400, "Empty question.")

    # 1) Retrieve
    retrieved = vectorstore.similarity_search(body.question, k=TOP_K)
    if not retrieved:
        return AskResponse(
            answer="No documents indexed yet. Upload a PDF first.",
            sources=[],
        )

    context = "\n\n---\n\n".join(d.page_content for d in retrieved)

    # 2) Generate
    llm = get_llm()
    prompt_text = PROMPT.format(context=context, question=body.question)
    resp = llm.invoke(prompt_text)
    answer = resp.content if hasattr(resp, "content") else str(resp)

    # 3) Shape sources for the UI
    sources = [
        Source(
            source=d.metadata.get("source", "unknown"),
            page=d.metadata.get("page"),
            snippet=d.page_content[:220] + ("..." if len(d.page_content) > 220 else ""),
        )
        for d in retrieved
    ]

    return AskResponse(answer=answer, sources=sources)
