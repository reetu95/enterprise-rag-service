# Enterprise RAG Service

A production-oriented Retrieval-Augmented Generation (RAG) backend built using FastAPI, OpenAI embeddings, and Chroma vector database.

This project demonstrates how to design and implement a scalable RAG pipeline capable of ingesting documents, generating embeddings, storing vector representations, and answering user queries using semantic search + LLM reasoning.

---

## 📌 Project Overview

This service allows users to:

- Upload TXT or PDF documents
- Parse and extract text (with optional OCR support)
- Chunk text into manageable segments
- Generate embeddings using OpenAI
- Store vectors in a persistent ChromaDB instance
- Retrieve top-K relevant chunks using semantic similarity
- Generate grounded answers using an LLM

The system is designed to be modular and production-ready, with clear separation between ingestion, vector storage, and retrieval layers.

---

## 🏗 System Architecture

![Architecture Diagram](docs/architecture.png)

### Architecture Explanation

1. **Client Request**
   - User uploads document or sends query.

2. **FastAPI Backend**
   - Handles routing, validation, and orchestration.

3. **Document Processing Pipeline**
   - File saved locally
   - Text extracted (TXT/PDF)
   - OCR (optional via Tesseract for scanned PDFs)
   - Text chunked into smaller segments

4. **Embedding Layer**
   - Each chunk converted to vector embeddings using:
     - `text-embedding-3-small`

5. **Vector Storage**
   - Embeddings stored in persistent ChromaDB.
   - Metadata stored alongside vectors (document_id, chunk_index).

6. **Query Flow**
   - User query converted to embedding.
   - Top-K similar chunks retrieved from vector store.
   - Retrieved context injected into LLM prompt.

7. **LLM Generation**
   - Response generated using:
     - `gpt-4o-mini`
   - Output returned to client.

---

### 🔎 Note on PostgreSQL

The architecture diagram includes an optional PostgreSQL layer.

Current implementation:
- Uses ChromaDB persistence
- Uses local filesystem storage for document tracking

PostgreSQL can be integrated in production to:
- Track ingestion tasks
- Store document metadata
- Maintain processing state
- Enable audit logging

This separation allows horizontal scaling and better observability in real-world deployments.

---

## 🔁 End-to-End Flow

### Document Upload

1. User uploads file (`/uploadfile`)
2. File saved to local storage
3. Text extracted
4. Text split into chunks
5. Each chunk embedded
6. Embeddings stored in Chroma

### Question Answering

1. User submits question (`/ask`)
2. Query converted to embedding
3. Top-K similar chunks retrieved
4. Context injected into prompt
5. LLM generates grounded response

---

## 🛠 Tech Stack

| Layer | Technology |
|--------|------------|
| API Framework | FastAPI |
| Embedding Model | OpenAI `text-embedding-3-small` |
| LLM | OpenAI `gpt-4o-mini` |
| Vector Store | ChromaDB (Persistent Mode) |
| OCR (Optional) | Tesseract |
| Language | Python 3.11 |

---

## 📂 Project Structure
