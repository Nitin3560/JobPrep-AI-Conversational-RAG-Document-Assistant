print("start main.py")
from fastapi import FastAPI
print("imported FastAPI")
from pydantic import BaseModel
print("imported BaseModel")
from fastapi import UploadFile, File, HTTPException, Body,Query
print("imported fastapi request helpers")
from pathlib import Path
print("imported Path")
import httpx
print("imported httpx")
import json
print("imported json")
from app.services.ingest import (
    load_text_from_txt,
    load_text_from_pdf,
    chunk_text_by_paragraphs,
    create_chunk_records,
)
print("imported ingest")

from app.services.embed_service import retrieve_chunks,embed_new_nodes,rag_chat
print("imported embed_service")
BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
STORAGE_DIR = BASE_DIR / "storage"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
CHUNKS_FILE = STORAGE_DIR / "chunks.jsonl"
USERS_FILE=STORAGE_DIR/"users.json"

from fastapi import UploadFile,File,HTTPException,Body,Query,Request

app = FastAPI()
print("created app")
from fastapi.middleware.cors import CORSMiddleware
print("imported CORS")

class LoginRequest(BaseModel):
    username:str
    password:str

def load_users()->list[dict]:
    if not USERS_FILE.exists():
        raise HTTPException(status_code=500,detail="users.json not found")
    data=json.loads(USERS_FILE.read_text(encoding="utf-8"))
    return data.get("users",[])

def get_user_by_username(username:str)->dict|None:
    users=load_users()
    for user in users:
        if user.get("username")==username:
            return user
    return None

def authenticate_user(username:str,password:str)->dict|None:
    users=load_users()
    for user in users:
        if user.get("username")==username and user.get("password")==password:
            return user
    return None

@app.post("/login")
def login(payload:LoginRequest):
    user=authenticate_user(payload.username,payload.password)
    if not user:
        raise HTTPException(status_code=401,detail="Invalid username or password")
    return {
        "username":user["username"],
        "role":user["role"],
        "message":"Login successful"
    }

@app.post("/logout")
def logout():
    return {"message":"Logout successful"}

def get_current_user(request:Request)->str:
    user=(request.headers.get("X-User") or "").strip()
    if not user:
        raise HTTPException(status_code=401,detail="Missing X-User header")
    matched_user=get_user_by_username(user)
    if not matched_user:
        raise HTTPException(status_code=401,detail="Unknown user")
    return matched_user["username"]
 
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://34.45.204.199:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
print("added CORS")
@app.get("/health")
def health_check():
    return {"status": "OK"}

class chatrequest(BaseModel):
    message:str

OLLAMA_BASE = "http://localhost:11434"
OLLAMA_MODEL = "llama3:8b"

@app.post("/chat")
async def chat(request:Request, payload: dict = Body(...)):
    user=get_current_user(request)
    user_message = (payload.get("message") or "").strip()
    job_description = (payload.get("job_description") or "").strip()
    top_k = int(payload.get("top_k", 3))

    if not user_message:
        return {"reply": "", "sources": []}

    try:
        out = rag_chat(user_message, owner=user, job_description=job_description, top_k=top_k)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "reply": out.get("answer", ""),
        "sources": out.get("sources", []),
    }


@app.post("/index")
def index():
    return {
        "status": "Indexing started"
    }

BASE_DIR=Path(__file__).resolve().parent.parent 
UPLOAD_DIR=BASE_DIR / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
print("UPLOAD_DIR =", UPLOAD_DIR.resolve())


def unique_path(directory: Path, filename: str) -> Path:
    original=Path(filename)
    stem=original.stem
    suffix=original.suffix
    candidate=directory/original.name
    if not candidate.exists():
        return candidate

    counter=2
    while True:
        candidate=directory/f"{stem}({counter}){suffix}"
        if not candidate.exists():
            return candidate
        counter+=1

@app.post("/upload")
async def upload(request:Request, file: UploadFile = File(...)):
    user=get_current_user(request)
    ext=Path(file.filename).suffix.lower()
    if ext not in {".txt",".pdf"}:
        raise HTTPException(status_code=400,detail="Only .txt and .pdf allowed")

    safe_name=Path(file.filename).name
    save_path=unique_path(UPLOAD_DIR,safe_name)
    contents=await file.read()
    save_path.write_bytes(contents)

    if ext==".txt":
        text=load_text_from_txt(str(save_path))
    else:
        text=load_text_from_pdf(str(save_path))

    if not text.strip():
        raise HTTPException(status_code=400,detail="Could not extract text from this file")

    chunks=chunk_text_by_paragraphs(text)
    records=create_chunk_records(chunks,str(save_path),user)
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)

    with CHUNKS_FILE.open("a", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r,ensure_ascii=False)+"\n")
    embed_stats = embed_new_nodes()
    return {
    "saved": True,
    "filename": save_path.name,
    "chunks_added": len(records),
    "embedded_now":embed_stats.get("embedded_now",0),
    "message":embed_stats.get("message","Indexing started"),
}

@app.get("/retrieve")
def retrieve(request:Request,
    q: str = Query(..., min_length=1),
    top_k: int = Query(3, ge=1, le=20),
):
    user=get_current_user(request)
    try:
        hits = retrieve_chunks(q, owner=user, top_k=top_k)
        return {"query": q, "top_k": top_k, "hits": hits}
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")

@app.post("/embed")
def embed():
    return embed_new_nodes()
