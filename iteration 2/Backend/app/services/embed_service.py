
from __future__ import annotations
print("start embed_service")
print("future done")
import hashlib
print("hashlib done")
import json
print("json done")
from pathlib import Path
print("pathlib done")
# from llama_index.core.schema import TextNode
# print("TextNode done")
# from llama_index.core import Settings,StorageContext,load_index_from_storage,VectorStoreIndex
# print("llama_index.core done")
# from llama_index.embeddings.ollama import OllamaEmbedding
# print("OllamaEmbedding done")
import httpx
print("httpx done")

BASE_DIR = Path(__file__).resolve().parents[2]
STORAGE_DIR = BASE_DIR / "storage"
CHUNKS_PATH = STORAGE_DIR / "chunks.jsonl"
EMBEDDED_IDS_PATH = STORAGE_DIR / "embedded_ids.json"
INDEX_DIR = STORAGE_DIR / "index"


def trim_text(text:str, limit:int)->str:
    text=(text or "").strip()
    if len(text)<=limit:
        return text
    return text[:limit].rsplit(" ",1)[0].strip()+"..."

def is_simple_greeting(text:str)->bool:
    text=(text or "").strip().lower()
    return text in {"hi","hello","hey","hy","hii","yo"}

def make_chunk_id(doc_id: str, text: str) -> str:
    doc_id=(doc_id or "").strip()
    text=(text or "").strip()
    raw=f"{doc_id}||{text}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()

def load_embedded_ids() -> set[str]:
    path=Path(EMBEDDED_IDS_PATH)
    if not path.exists():
        return set()

    data=json.loads(path.read_text(encoding="utf-8"))
    ids=data.get("embedded_ids", [])
    return set(ids)

def save_embedded_ids(ids: set[str]) -> None:
    path=Path(EMBEDDED_IDS_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    data={"embedded_ids": sorted(ids)}
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")

def collect_new_nodes() -> tuple[list["TextNode"], set[str], dict]:
    from llama_index.core.schema import TextNode
    embedded=load_embedded_ids()
    chunks_path=Path(CHUNKS_PATH)
    if not chunks_path.exists():
        return [], set(), {"total_read": 0, "skipped": 0, "new_found": 0}

    new_nodes:list[TextNode] = []
    new_ids:set[str] = set()
    total_read=0
    skipped=0
    with chunks_path.open("r", encoding="utf-8") as f:
        for line in f:
            line=line.strip()
            if not line:
                continue
            total_read+=1
            record=json.loads(line)
            doc_id=(record.get("doc_id") or "").strip()
            text=(record.get("text") or "").strip()
            owner=(record.get("owner") or "").strip()
            if not text:
                continue
            chunk_id=make_chunk_id(doc_id, text)
            if chunk_id in embedded:
                skipped+=1
                continue
            node=TextNode(
                text=text,
                metadata={
                    "doc_id":doc_id,
                    "chunk_id":chunk_id,
                    "source":(record.get("source") or doc_id),
                    "owner":owner,
                },
            )
            new_nodes.append(node)
            new_ids.add(chunk_id)
    stats={"total_read": total_read, "skipped": skipped, "new_found": len(new_nodes)}
    return new_nodes, new_ids, stats

def embed_new_nodes() -> dict:
    from llama_index.core import Settings, StorageContext, load_index_from_storage, VectorStoreIndex
    from llama_index.embeddings.ollama import OllamaEmbedding
    Settings.embed_model=OllamaEmbedding(model_name="nomic-embed-text")
    new_nodes, new_ids, stats=collect_new_nodes()
    if not new_nodes:
        return {**stats, "embedded_now": 0, "message": "No new chunks to embed."}

    index_dir=Path(INDEX_DIR)
    index_dir.mkdir(parents=True, exist_ok=True)
    if any(index_dir.iterdir()):
        storage_context=StorageContext.from_defaults(persist_dir=str(index_dir))
        index=load_index_from_storage(storage_context)
    else:
        index=VectorStoreIndex([])

    index.insert_nodes(new_nodes)
    index.storage_context.persist(persist_dir=str(index_dir))
    embedded=load_embedded_ids()
    embedded.update(new_ids)
    save_embedded_ids(embedded)

    return {**stats, "embedded_now": len(new_nodes), "message": "Embedded and persisted successfully."}

def retrieve_chunks(query:str, owner:str, top_k:int=3)->list[dict]:
    from llama_index.core import Settings, StorageContext, load_index_from_storage
    from llama_index.embeddings.ollama import OllamaEmbedding
    Settings.embed_model = OllamaEmbedding(model_name="nomic-embed-text")
    index_dir=Path(INDEX_DIR)
    if not index_dir.exists() or not any(index_dir.iterdir()):
        raise FileNotFoundError(
            f"Index not found or empty at {INDEX_DIR}. Run embedding first."
        )
    storage_context=StorageContext.from_defaults(persist_dir=str(index_dir))
    index=load_index_from_storage(storage_context)
    candidate_k=max(top_k*3,12)
    retriever=index.as_retriever(similarity_top_k=candidate_k)
    results=retriever.retrieve(query)
    out:list[dict]=[]
    for r in results:
        node=r.node
        node_owner=(node.metadata.get("owner") or "").strip()
        if node_owner!=owner:
            continue
        out.append(
            {
                "score":float(getattr(r, "score", 0.0)),
                "doc_id":node.metadata.get("doc_id"),
                "chunk_id":node.metadata.get("chunk_id"),
                "owner":node_owner,
                "text":node.get_content(),
            }
        )
        if len(out)>=top_k:
            break
    return out

def ollama_generate(model: str, prompt: str) -> str:
    url="http://localhost:11434/api/generate"
    payload={"model": model, "prompt": prompt, "stream": False}
    r=httpx.post(url, json=payload, timeout=240)
    r.raise_for_status()
    return r.json().get("response", "").strip()

def rag_chat(question: str, owner:str, job_description:str="", top_k: int = 3) -> dict:
    if is_simple_greeting(question):
        return {
            "question": question,
            "top_k": 0,
            "answer": "Hi! Paste the job description you want to prepare for, then ask your job application questions.",
            "sources": [],
        }

    hits = retrieve_chunks(question, owner=owner, top_k=top_k)

    sources = [
        {
            "doc_id": h["doc_id"],
            "chunk_id": h["chunk_id"],
            "score": h["score"],
            "text": h["text"],
            "snippet": h["text"][:240],
        }
        for h in hits
    ]

    sources_block = "\n\n".join(
        f"[{s['chunk_id']}] {trim_text(s['snippet'], 180)}" for s in sources
    )
    system = (
    "You are Job Application Helper.\n"
    "Use the uploaded user material as the main source of truth.\n"
    "Use the active job description to tailor the answer when relevant.\n"
    "Do not invent user-specific experience, projects, skills, achievements, or results that are not supported by the context.\n"
    "If important user-specific details are missing, ask a short follow-up instead of assuming.\n"
    "Be direct and practical. Prefer short bullet points when helpful.\n"
    )

    context = sources_block
    active_job_description = trim_text(job_description, 1200) if job_description else "None"

    prompt = (
    f"{system}\n\n"
    f"JOB DESCRIPTION:\n{active_job_description}\n\n"
    f"USER MATERIAL:\n{context or 'None'}\n\n"
    f"QUESTION:\n{question}\n\n"
    "Answer directly. If details are missing, ask one short follow-up.\n\n"
    "ANSWER:\n"
    )

    answer = ollama_generate(model="qwen2.5:3b", prompt=prompt)

    return {
        "question": question,
        "top_k": top_k,
        "answer": answer,
        "sources": [
            {"doc_id": s["doc_id"], "chunk_id": s["chunk_id"], "score": s["score"],"snippet": s["text"][:240]}
            for s in sources
        ],
    }
