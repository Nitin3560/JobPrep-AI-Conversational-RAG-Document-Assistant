# JobPrep-AI-Conversational-RAG-Document-Assistant

## Demo

▶️ **Demo Video:** https://youtu.be/LgAuwA7_3VM


## Overview

Job Application Helper is an AI-powered system designed to assist users during the job application process by generating context-aware, grounded responses to common application questions (e.g., “Why this role?”, project explanations, experience summaries).

The system is built using a **Retrieval-Augmented Generation (RAG)** architecture, ensuring that responses are derived strictly from user-provided documents such as resumes, project descriptions, and notes — rather than relying on generic language model behavior.

This project was built end-to-end with a focus on **system correctness, debuggability, and reliability**, not automation for its own sake.

---

## Key Features

- Document upload with automated text extraction
- Intelligent chunking and semantic embedding
- Vector-based similarity search for relevant context
- Context-aware conversational interface
- Incremental indexing without rebuilding the full vector store
- Strict pipeline state enforcement (Upload → Chunk → Embed → Retrieve)
- Modular and extensible backend architecture

---

## Tech Stack

**Backend**
- Python
- FastAPI
- Local LLM integration
- Vector store (local)
- REST APIs
- Structured logging

**Frontend**
- Lightweight web UI for chat and document upload
- Strict response schema enforcement

**Other**
- JSON-based metadata tracking
- Local storage (no cloud dependencies)
- Git-based version control

---

## System Architecture (High Level)

1. **Upload**  
   User uploads documents (resume, project notes, etc.)

2. **Chunking**  
   Documents are split into semantically meaningful chunks with stable IDs

3. **Embedding**  
   Chunks are embedded and stored in a vector index

4. **Retrieval**  
   Relevant chunks are retrieved based on query similarity

5. **Generation**  
   LLM generates responses grounded strictly in retrieved context

---

## Engineering Challenges & Lessons

While building the system, several non-trivial engineering challenges surfaced. Below are the most meaningful ones and how they were resolved.

### 1. RAG Pipeline Ordering Failures
Retrieval was occasionally executed before embeddings were generated, resulting in empty or misleading responses.

**Resolution:**  
Enforced a strict system state workflow with explicit precondition checks:
Upload → Chunk → Embed → Retrieve


### 2. Silent Retrieval Failures and Hallucinated Outputs
When retrieval returned low-signal or empty results, the LLM still produced confident but incorrect responses.

**Resolution:**  
Added index readiness checks and converted silent failures into explicit, surfaced errors rather than allowing generation to proceed.


### 3. Chunk Identity Mismatches Across Storage Layers
Retrieved chunks did not always map back correctly to the source text due to inconsistent chunk IDs between storage and the vector index.

**Resolution:**  
Standardized chunk ID generation and metadata schema across ingestion, storage, and retrieval layers.


### 4. Duplicate Embeddings and Wasted Compute
Re-uploading documents resulted in redundant embeddings without visibility into previously processed chunks.

**Resolution:**  
Implemented persistent chunk tracking using an `embedded_ids.json` file to prevent re-embedding already indexed content.


### 5. Backend Failures Masked by Frontend Behavior
The frontend appeared functional even when backend services were failing silently, leading to confusing user experiences.

**Resolution:**  
Locked backend response contracts and propagated backend errors explicitly to the frontend for visibility.


### 6. Poor Observability During Failures
Minimal logging made it difficult to determine which stage of the pipeline failed during errors.

**Resolution:**  
Introduced stage-level logging for ingestion, embedding, and retrieval to isolate failures quickly.


### 7. Environment-Dependent Behavior and Brittle Setup
The application behaved inconsistently across machines due to hard-coded paths and environment drift.

**Resolution:**  
Standardized environment setup, removed absolute paths, and documented strict startup and execution order.

---

## What This Project Demonstrates

- Practical understanding of RAG system design
- Backend architecture and API design
- Debugging distributed-style pipelines
- Failure-mode analysis and prevention
- Engineering discipline beyond simple LLM usage

---

## Current Limitations

- No automated test suite yet (manual validation scripts used)
- Single-user local setup
- No cloud deployment (by design for learning purposes)

---

## Future Improvements

- Automated integration tests for each pipeline stage
- Better retrieval evaluation metrics
- Multi-document prioritization strategies
- Optional cloud deployment

---

## Setup & Running the Project 
This project is designed to run **locally** to better understand system behavior, failure modes, and design trade-offs. 
### Prerequisites 
- Python 3.10+
- pip
- Git


### 1. Clone the Repository 
```bash
git clone https://github.com/<your-username>/Job-Application-Helper-AI-Powered-RAG-System.git  
cd Job-Application-Helper-AI-Powered-RAG-System 
```

### 2. Backend Setup  
```bash
cd Backend  
python -m venv  
.venv source .venv/bin/activate (for Windows .venv\Scripts\activate)  
pip install -r requirements.txt
```
### 3. Start the Backend Server 
```bash
uvicorn app.main:app --reload
```
By default, the backend runs at: http://127.0.0.1:8000
### 4. Frontend Setup 
In a new terminal: 
```bash
cd Frontend  
npm install  
npm run dev
```
The frontend runs at: http://localhost:5173 

### 5. Using the Application

- Open the frontend in your browser  
- Upload a resume or project document  
- Trigger embedding (only new documents are embedded)  
- Ask questions via the chat interface 

#### Responses are generated using the retrieved document context
---

## Disclaimer

This project is intended as a **learning-focused systems build**, not a production SaaS application. The emphasis is on understanding system behavior, failure modes, and architectural trade-offs.
