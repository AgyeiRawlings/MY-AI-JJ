"""
GPT-5/6 Style Streaming Coding Assistant (Gradio fixed)
- Enter key and Send button work
- Chat auto-clears textbox after sending
- Streaming works properly
- Auto-scrolls to latest message
"""

import os
import json
import pickle
import faiss
import threading
from sentence_transformers import SentenceTransformer
from openai import OpenAI
import gradio as gr

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
# OpenAI client
# -----------------------------
client = OpenAI(api_key=OPENAI_API_KEY)

# -----------------------------
# Embedding model
# -----------------------------
embed_model = SentenceTransformer(EMBEDDING_MODEL)

# -----------------------------
# Threading locks
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
# Semantic search
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
            old_messages = context[:-SUMMARY_LIMIT]
            text_to_summarize = "\n".join([m.get("content","") for m in old_messages])
            prompt = f"Summarize this conversation concisely (bullet points) for coding assistant context:\n\n{text_to_summarize}"
            try:
                response = client.chat.completions.create(
                    model=OPENAI_MODEL,
                    messages=[{"role":"user","content":prompt}],
                    max_tokens=200,
                    temperature=0.3
                )
                summary = response.choices[0].message.content.strip()
            except Exception as e:
                print(f"[WARN] summarization failed: {e}")
                return
            context[:] = [{"role":"system_summary","content":summary}] + context[-SUMMARY_LIMIT:]
            try:
                with open(CONTEXT_FILE,"w",encoding="utf-8") as f:
                    json.dump(context,f,ensure_ascii=False,indent=2)
            except Exception as e:
                print(f"[WARN] failed to write context: {e}")

# -----------------------------
# Generate response streaming
# -----------------------------
def generate_response_stream(user_input):
    with context_lock:
        context.append({"role":"user","content":user_input})
    summarize_context()
    relevant_facts = "\n".join(retrieve_knowledge(user_input))
    with context_lock:
        context_text = "\n".join([m.get("content","") for m in context[-SUMMARY_LIMIT:]])

    answer_prompt = f"""
You are a coding assistant AI. Answer the question with working code, explanations, and optimizations.

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
            stream_resp = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[{"role":"user","content":answer_prompt}],
                temperature=TEMPERATURE,
                stream=True
            )
            for chunk in stream_resp:
                delta = chunk.choices[0].delta
                dcont = getattr(delta,"content",None) if hasattr(delta,"content") else delta.get("content") if isinstance(delta,dict) else None
                if dcont:
                    final_text += dcont
                    yield final_text
        except Exception as e:
            yield f"[ERROR] Streaming failed: {e}"

        with context_lock:
            context.append({"role":"assistant","content":final_text})
            try:
                with open(CONTEXT_FILE,"w",encoding="utf-8") as f:
                    json.dump(context,f,ensure_ascii=False,indent=2)
            except Exception as e:
                print(f"[WARN] failed saving context: {e}")

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
                print(f"[WARN] failed writing index: {e}")
        try:
            with open(KNOWLEDGE_FILE,"wb") as f:
                pickle.dump(knowledge,f)
        except Exception as e:
            print(f"[WARN] failed writing knowledge file: {e}")
    return f"**Knowledge added:** `{new_fact}`"

# -----------------------------
# Gradio Blocks interface
# -----------------------------
with gr.Blocks() as demo:
    chatbot = gr.Chatbot()
    state = gr.State([])
    msg = gr.Textbox(lines=2, placeholder="Ask a coding question...")
    submit_btn = gr.Button("Send")

    def respond(user_input, history):
        history = history or []
        if not user_input:
            return history, history, ""
        if user_input.lower().startswith("add "):
            added = add_knowledge(user_input[4:].strip())
            history.append([user_input, added])
            return history, history, ""
        history.append([user_input,""])
        for partial in generate_response_stream(user_input)():
            history[-1][1] = partial
            yield history, history, ""  # auto-clear textbox

    # Connect Enter key & Send button
    msg.submit(respond, inputs=[msg,state], outputs=[chatbot,state,msg])
    submit_btn.click(respond, inputs=[msg,state], outputs=[chatbot,state,msg])

# -----------------------------
# Launch
# -----------------------------
if __name__ == "__main__":
    demo.launch()
