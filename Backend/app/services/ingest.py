import json
from pypdf import PdfReader

def load_text_from_txt(file_path:str)->str:
    with open(file_path, 'r', encoding='utf-8') as file:
        text = file.read()
        text = text.replace("\r\n","\n")
        text=text.replace("\r","\n")
        while "\n\n\n" in text:
            text=text.replace("\n\n\n","\n\n")
        text = text.strip()
    return text

def load_text_from_pdf(file_path:str)->str:
    reader=PdfReader(file_path)
    parts=[]
    for page in reader.pages:
        t=page.extract_text() or ""
        parts.append(t)
    text="\n".join(parts)
    text=text.replace("\r\n","\n").replace("\r","\n")
    while "\n\n\n" in text:
        text=text.replace("\n\n\n","\n\n")
    return text.strip()

def chunk_text_by_paragraphs(text:str, max_chars: int =1200, overlap: int =200)-> list[str]:
    paragraphs=[]
    chunks=[]
    paragraphs = text.split("\n\n")
    for paragraph in paragraphs:
        if paragraph.strip()!="":
            chunks.append(paragraph.strip())

    final_chunks = []
    current = ""

    for p in chunks:
        if current=="":
            current=p
            continue

        attempt=current+"\n\n"+p

        if len(attempt)<=max_chars:
            current=attempt
        else:
            final_chunks.append(current)
            tail=current[-overlap:] if overlap>0 else ""
            current=tail+"\n\n"+p

    if current:
        final_chunks.append(current)
    
    print(len(final_chunks))
    return final_chunks

def create_chunk_records(final_chunks: list[str], source_file: str, owner:str) -> list[dict]:
    records = []
    for i, chunk in enumerate(final_chunks):
        record = {
            "doc_id": f"{source_file}",
            "text": chunk,
            "source": source_file,
            "chunk_id": i,
            "owner": owner
        }
        records.append(record)
    return records

def write_chunks_jsonl(chunks_path, records):
    with open(chunks_path, 'w', encoding='utf-8')as f:
        for record in records:
            json_line=json.dumps(record, ensure_ascii=False)
            f.write(json_line + "\n")

def create_index_summary(final_chunks: list[str], source_file: str) -> dict:
    summary_dict = {
        "source_file": source_file,
        "total_chunks": len(final_chunks),
        "chunks": []
    }
    for i, chunk in enumerate(final_chunks):
        chunk_info = {
            "chunk_id": i,
            "char_count": len(chunk)
        }
        summary_dict["chunks"].append(chunk_info)
    return summary_dict

def write_index_summary(summary_path, summary_dict):
    with open(summary_path, 'w', encoding='utf-8') as f:
        json_text = json.dumps(summary_dict, indent=2, ensure_ascii=False)
        f.write(json_text)

