# model.py
"""
Rawling JJ AI - AI logic and streaming responses
"""

import os
import json
import pickle
import faiss
import threading
from sentence_transformers import SentenceTransformer
from openai import OpenAI

# -----------------------------
# Configuration
# -----------------------------
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "YOUR_OPENAI_API_KEY")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
KNOWLEDGE_FILE = "knowledge.pkl"
INDEX_FILE = "faiss_index_hnsw.index"
CONTEXT_FILE = "context.json"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
TOP_K = 5
MEMORY_LIMIT = 50
SUMMARY_LIMIT = 20
TEMPERATURE = 0.7

# -----------------------------
# OpenAI client & embedding model
# -----------------------------
client = OpenAI(api_key=OPENAI_API_KEY)
embed_model = SentenceTransformer(EMBEDDING_MODEL)

# -----------------------------
# Thread locks
# -----------------------------
context_lock = threading.Lock()
index_lock = threading.Lock()
knowledge_lock = threading.Lock()

# -----------------------------
# Load/create knowledge base
# -----------------------------
if os.path.exists(KNOWLEDGE_FILE) and os.path.exists(INDEX_FILE):
    with open(KNOWLEDGE_FILE, "rb") as f:
        knowledge = pickle.load(f)
    index = faiss.read_index(INDEX_FILE)
else:
    knowledge = [
        "Python programming and debugging tips.",
        "How to fix common errors in code.",
        "General computer troubleshooting steps.",
        "AI, machine learning, and coding best practices."
    ]
    embeddings = embed_model.encode(knowledge, convert_to_numpy=True)
    dim = embeddings.shape[1]
    index = faiss.IndexHNSWFlat(dim, 32)
    index.add(embeddings)
    with open(KNOWLEDGE_FILE, "wb") as f:
        pickle.dump(knowledge, f)
    faiss.write_index(index, INDEX_FILE)

# -----------------------------
# Load/create conversation context
# -----------------------------
if os.path.exists(CONTEXT_FILE):
    with open(CONTEXT_FILE, "r", encoding="utf-8") as f:
        context = json.load(f)
else:
    context = []

# -----------------------------
# Retrieve knowledge
# -----------------------------
def retrieve_knowledge(query, top_k=TOP_K):
    vec = embed_model.encode([query], convert_to_numpy=True)
    with index_lock:
        D, I = index.search(vec, top_k)
    return [knowledge[i] for i in I[0] if i < len(knowledge)]

# -----------------------------
# Summarize context
# -----------------------------
def summarize_context():
    with context_lock:
        if len(context) > MEMORY_LIMIT:
            old_msgs = context[:-SUMMARY_LIMIT]
            text_to_summarize = "\n".join([m.get("content","") for m in old_msgs])
            prompt = f"Summarize this conversation concisely in bullet points:\n\n{text_to_summarize}"
            try:
                response = client.chat.completions.create(
                    model=OPENAI_MODEL,
                    messages=[{"role":"user","content":prompt}],
                    max_tokens=200,
                    temperature=0.3
                )
                summary = response.choices[0].message.content.strip()
            except Exception as e:
                print(f"[WARN] Summarization failed: {e}")
                return
            context[:] = [{"role":"system_summary","content":summary}] + context[-SUMMARY_LIMIT:]
            try:
                with open(CONTEXT_FILE,"w",encoding="utf-8") as f:
                    json.dump(context,f,ensure_ascii=False,indent=2)
            except Exception as e:
                print(f"[WARN] Failed saving context: {e}")

# -----------------------------
# Generate streaming response
# -----------------------------
def generate_response_stream(user_input):
    with context_lock:
        context.append({"role":"user","content":user_input})
    summarize_context()
    relevant_facts = "\n".join(retrieve_knowledge(user_input))
    with context_lock:
        context_text = "\n".join([m.get("content","") for m in context[-SUMMARY_LIMIT:]])

    prompt = f"""
You are a highly capable coding assistant AI. Provide working code, explanations, optimizations, and emojis.

Question: {user_input}
Facts:
{relevant_facts}
Context:
{context_text}

Answer:
"""

    def stream():
        final_text = ""
        try:
            resp = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[{"role":"user","content":prompt}],
                temperature=TEMPERATURE,
                stream=True
            )
            for chunk in resp:
                delta = chunk.choices[0].delta
                d = getattr(delta,"content",None) if hasattr(delta,"content") else delta.get("content") if isinstance(delta,dict) else None
                if d:
                    final_text += d
                    yield final_text
        except Exception as e:
            yield f"[ERROR] {e}"

        with context_lock:
            context.append({"role":"assistant","content":final_text})
            try:
                with open(CONTEXT_FILE,"w",encoding="utf-8") as f:
                    json.dump(context,f,ensure_ascii=False,indent=2)
            except Exception as e:
                print(f"[WARN] Failed saving context: {e}")

    return stream

# -----------------------------
# Add knowledge dynamically
# -----------------------------
def add_knowledge(new_fact):
    with knowledge_lock:
        knowledge.append(new_fact)
        vec = embed_model.encode([new_fact], convert_to_numpy=True)
        with index_lock:
            index.add(vec)
            try:
                faiss.write_index(index, INDEX_FILE)
            except Exception as e:
                print(f"[WARN] Failed writing index: {e}")
        try:
            with open(KNOWLEDGE_FILE,"wb") as f:
                pickle.dump(knowledge,f)
        except Exception as e:
            print(f"[WARN] Failed writing knowledge file: {e}")
    return f"**Knowledge added:** `{new_fact}`"

# -----------------------------
# Simple server.py compatibility
# -----------------------------
def get_response(message):
    return f"💡 AI: {message}"
