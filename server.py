import os, uuid, nltk
from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone

nltk.download('punkt')

# Pinecone config (hardcoded keys)
PINECONE_API_KEY = "pcsk_5TVd2A_Jo61kevFCh53TfWzDqe4rccSre3nC7K2sF3eZAAZagZ9LHhmahcPHzM17jVF4ad"
INDEX_NAME = "resume-index"

# Initialize Pinecone client
pc = Pinecone(api_key=PINECONE_API_KEY)

# Create index if it doesn't exist
if INDEX_NAME not in pc.list_indexes().names():
    pc.create_index(
        name=INDEX_NAME,
        dimension=384,
        metric="cosine"
    )

# Connect to index
index = pc.Index(INDEX_NAME)

# Load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

app = FastAPI(title="ResumePro Vector Search")

# Models
class IngestRequest(BaseModel):
    doc_id: str
    text: str

class SearchRequest(BaseModel):
    text: str
    top_k: int = 5

# --- Chunking function ---
def chunk_text_fn(text, chunk_size=1000, overlap=200):
    from nltk.tokenize import sent_tokenize
    sentences = sent_tokenize(text)
    chunks = []
    cur = ""
    for s in sentences:
        if len(cur) + len(s) + 1 <= chunk_size:
            cur = (cur + " " + s).strip()
        else:
            if cur:
                chunks.append(cur)
            cur = s
    if cur:
        chunks.append(cur)
    # Add overlap between chunks
    merged = []
    for i, c in enumerate(chunks):
        if i == 0:
            merged.append(c)
        else:
            merged.append(chunks[i-1][-overlap:] + " " + c)
    return merged

# --- Ingest endpoint ---
@app.post("/ingest")
def ingest(req: IngestRequest):
    chunks = chunk_text_fn(req.text)  # Use correct function
    vectors = model.encode(chunks)
    upserts = []
    for idx, (chunk, vector) in enumerate(zip(chunks, vectors)):  # Rename loop variable to avoid shadowing
        vector_id = f"{req.doc_id}__{idx}"
        payload = {"doc_id": req.doc_id, "chunk_index": idx, "text": chunk}
        upserts.append((vector_id, vector.tolist(), payload))
    index.upsert(vectors=upserts)
    return {"status": "ok", "chunks_indexed": len(upserts)}

# --- Search endpoint ---
@app.post("/search")
def search(req: SearchRequest):
    query_vector = model.encode([req.text])[0].tolist()
    results = index.query(vector=query_vector, top_k=req.top_k, include_metadata=True)
    out = []
    for match in results['matches']:
        out.append({
            "id": match['id'],
            "score": match['score'],
            "doc_id": match['metadata']['doc_id'],
            "chunk_index": match['metadata']['chunk_index'],
            "text": match['metadata']['text']
        })
    return {"query": req.text, "results": out}

@app.get("/health")
def health():
    return {"ok": True}
