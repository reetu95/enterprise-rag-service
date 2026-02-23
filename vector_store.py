import os
import uuid
import chromadb
from chromadb.config import Settings
from openai import OpenAI
from dotenv import load_dotenv

# Load .env so OPENAI_API_KEY is available (but still don't create client globally)
load_dotenv()

# --------------------
# Chroma (persistent)
# --------------------
chroma_client = chromadb.Client(
    Settings(persist_directory="./chroma_db", anonymized_telemetry=False)
)

collection = chroma_client.get_or_create_collection(name="chunks")

# --------------------
# OpenAI client (lazy / safe)
# --------------------
def get_openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set. Add it to your .env file.")
    return OpenAI(api_key=api_key)

# --------------------
# Embeddings + Vector store ops
# --------------------
def embed_text(text: str) -> list[float]:
    client = get_openai_client()
    resp = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return resp.data[0].embedding


def add_chunks(document_id: str, chunks: list[str]) -> int:
    ids: list[str] = []
    docs: list[str] = []
    embs: list[list[float]] = []
    metadatas: list[dict] = []

    for i, chunk in enumerate(chunks):
        if not chunk or not chunk.strip():
            continue

        chunk_id = f"{document_id}_chunk_{i}_{uuid.uuid4().hex[:8]}"
        ids.append(chunk_id)
        docs.append(chunk)
        embs.append(embed_text(chunk))
        metadatas.append({"document_id": document_id, "chunk_index": i})

    if not ids:
        return 0

    collection.add(ids=ids, documents=docs, embeddings=embs, metadatas=metadatas)
    chroma_client.persist()
    return len(ids)


def query_chunks(query: str, top_k: int = 4, document_id: str | None = None) -> list[str]:
    q_emb = embed_text(query)

    where_filter = {"document_id": document_id} if document_id else None

    res = collection.query(
        query_embeddings=[q_emb],
        n_results=top_k,
        where=where_filter
    )

    # Chroma returns documents as List[List[str]]
    docs = res.get("documents") or []
    return docs[0] if docs else []