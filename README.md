# JobPrep AI

Conversational RAG assistant that reads a candidate's resume and generates personalized, context-aware answers for job application questions. Runs fully offline via Ollama — no external API dependency or data sent to third-party services.

The problem it solves: most candidates copy-paste generic answers into job applications or rewrite the same points from scratch for every role. JobPrep reads what you have actually done and generates answers grounded in your own experience, matched to the question being asked.

![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=flat&logo=javascript&logoColor=black)
![GCP](https://img.shields.io/badge/GCP-4285F4?style=flat&logo=googlecloud&logoColor=white)

## How it works

**Document ingestion** - resume and supporting documents are uploaded, parsed, and chunked. `ingest.py` handles document processing and passes content to the embedding pipeline.

**Embedding and indexing** - `embed_service.py` generates vector embeddings using LlamaIndex and stores them in a local index. Incremental embedding logic means only new or changed content gets re-embedded on subsequent uploads, improving indexing efficiency by 45%.

**Conversational retrieval** - when a user submits an application question, the query is embedded, matched against the document index using vector search, and the most relevant chunks are retrieved. The local Ollama LLM then generates a grounded, personalized answer from those chunks, sub-2 second end-to-end response times.

**Frontend** - React-based UI for document upload, question input, and answer review. Deployed on GCP and serving 12-15 active users.

## What makes it different from a generic LLM prompt

A generic "write me a cover letter" prompt has no grounding; it fabricates specifics or stays vague. JobPrep retrieves actual content from the candidate's documents before generating, so answers reference real projects, real metrics, and real experience. The candidate reviews and edits, not rewrites from scratch.

## Iterations

**Iteration 1** - core RAG pipeline with document ingestion, LlamaIndex vector search, and Ollama inference Single-user, local only.

**Iteration 2** - full-stack application with FastAPI backend, React frontend, GCP deployment, multi-user support, and incremental embedding for faster re-indexing.

## Structure

```
iteration 2/
  Backend/
    app/
      services/     embed_service, ingest pipeline
      routes/       FastAPI route handlers
    data/           document storage
    storage/        vector index storage
  Frontend/         React UI
  Demo/             demo materials
```
