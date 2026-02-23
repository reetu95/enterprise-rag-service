from fastapi import FastAPI, UploadFile, HTTPException, File
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI

import os
import uuid
import logging

# ---- NEW imports for parsing + chunking + Chroma ----
from file_parser import FileParser
from chunker import chunk_text
from vector_store import add_chunks, query_chunks

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# --------------------
# Load env + OpenAI client
# --------------------
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is not set. Add it to your .env file.")

client = OpenAI(api_key=OPENAI_API_KEY)

# --------------------
# Upload config
# --------------------
ALLOWED_EXTENSIONS = {".pdf", ".txt"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
UPLOAD_FOLDER = "sources"

class QuestionRequest(BaseModel):
    question: str
    # Optional: restrict retrieval to a specific uploaded doc
    document_id: str | None = None

@app.get("/")
def root():
    return {"message": "Hello RAG fellow!"}

@app.post("/uploadfile/")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is missing.")

    _, ext = os.path.splitext(file.filename)
    ext = ext.lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Only {ALLOWED_EXTENSIONS} files are allowed.")

    content = await file.read()

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 10MB.")

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    safe_filename = f"{uuid.uuid4()}{ext}"
    file_location = os.path.join(UPLOAD_FOLDER, safe_filename)

    try:
        with open(file_location, "wb") as f:
            f.write(content)
    except Exception as e:
        logger.error(f"File upload failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error saving file")

    logger.info(f"File saved: {safe_filename}")

    # --------------------
    # NEW: Parse → Chunk → Store in Chroma
    # --------------------
    try:
        extracted_text = FileParser(file_location).parse()
        chunks = chunk_text(extracted_text)

        document_id = safe_filename  # simplest stable doc id for now
        chunks_indexed = add_chunks(document_id=document_id, chunks=chunks)

        logger.info(f"Indexed doc_id={document_id} chunks={chunks_indexed}")
    except Exception as e:
        # File is saved, but indexing failed
        logger.error(f"Indexing failed for {safe_filename}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="File saved but indexing failed")

    return {
        "info": "File saved and indexed",
        "document_id": document_id,
        "original_filename": file.filename,
        "stored_filename": safe_filename,
        "size_bytes": len(content),
        "chunks_indexed": chunks_indexed,
    }

@app.post("/ask")
async def ask(req: QuestionRequest):
    """
    Real RAG (with Chroma):
    - Retrieve top chunks from vector store
    - Answer using ONLY retrieved evidence
    """
    try:
        evidence_chunks = query_chunks(
            query=req.question,
            top_k=4,
            document_id=req.document_id
        )
        evidence_text = "\n\n---\n\n".join(evidence_chunks)

        prompt = (
            "You are a helpful assistant.\n"
            "Use ONLY the evidence below. If the answer is not in the evidence, say \"I don't know\".\n\n"
            f"EVIDENCE:\n{evidence_text}\n\n"
            f"QUESTION:\n{req.question}\n\n"
            "ANSWER:"
        )

        resp = client.responses.create(
            model="gpt-4o-mini",
            input=prompt,
        )

        return {
            "answer": resp.output_text,
            "used_chunks": len(evidence_chunks),
            "document_filter": req.document_id,
        }
    except Exception as e:
        logger.error(f"/ask failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/embed")
async def embed(req: QuestionRequest):
    """
    Embedding endpoint (kept).
    """
    try:
        emb = client.embeddings.create(
            model="text-embedding-3-small",
            input=req.question,
        )
        vector = emb.data[0].embedding
        return {"embedding_dim": len(vector)}
    except Exception as e:
        logger.error(f"/embed failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))