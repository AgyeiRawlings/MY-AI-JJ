# app.py
import streamlit as st
import openai
from io import BytesIO
from tempfile import NamedTemporaryFile
import subprocess
from PIL import Image
import pytesseract
import PyPDF2
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

# =========================
# CONFIGURATION
# =========================
st.set_page_config(page_title="Rawlings JJ - AI Assistant", layout="wide")
st.title("Rawlings JJ - AI Assistant")

# Load OpenAI API key
try:
    openai.api_key = st.secrets["OPENAI_API_KEY"]
except KeyError:
    st.error("OpenAI API key not found in Streamlit secrets. Please add it as OPENAI_API_KEY.")
    st.stop()

# =========================
# VECTOR MEMORY INITIALIZATION
# =========================
if 'vector_index' not in st.session_state:
    st.session_state.vector_index = faiss.IndexFlatL2(384)  # 384-dim embeddings
    st.session_state.documents = []

if 'model' not in st.session_state:
    st.session_state.model = SentenceTransformer('all-MiniLM-L6-v2')

# =========================
# FUNCTIONS
# =========================
def chat_with_ai(user_input, use_memory=False):
    """Chat with OpenAI GPT models using updated API"""
    try:
        prompt = user_input
        if use_memory and st.session_state.documents:
            # Retrieve top relevant knowledge
            query_embedding = st.session_state.model.encode([user_input])
            D, I = st.session_state.vector_index.search(np.array(query_embedding).astype('float32'), k=3)
            retrieved_texts = [st.session_state.documents[i] for i in I[0] if i < len(st.session_state.documents)]
            if retrieved_texts:
                context = "\n---\n".join(retrieved_texts)
                prompt = f"Use this knowledge to answer the question:\n\n{context}\n\nQuestion: {user_input}"

        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message['content']
    except Exception as e:
        return f"Error: {e}"

def transcribe_audio(audio_file):
    """Transcribe audio using Whisper API"""
    try:
        audio_file.seek(0)
        transcript = openai.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
        return transcript.text
    except Exception as e:
        return f"Error: {e}"

def run_python_code(code):
    """Execute Python code safely"""
    try:
        with NamedTemporaryFile(delete=False, suffix=".py") as tmpfile:
            tmpfile.write(code.encode("utf-8"))
            tmpfile.flush()
            result = subprocess.run(["python", tmpfile.name], capture_output=True, text=True, timeout=10)
        return result.stdout + result.stderr
    except Exception as e:
        return f"Error: {e}"

def ocr_image(image_file):
    """Extract text from image"""
    try:
        img = Image.open(image_file)
        text = pytesseract.image_to_string(img)
        return text if text.strip() else "No text detected in image."
    except Exception as e:
        return f"OCR Error: {e}"

def extract_pdf_text(pdf_file):
    """Extract text from PDF"""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = "".join(page.extract_text() or "" for page in pdf_reader.pages)
        return text if text.strip() else "No text detected in PDF."
    except Exception as e:
        return f"PDF Extraction Error: {e}"

def add_to_vector_memory(text):
    """Add text to vector memory"""
    embedding = st.session_state.model.encode([text])
    st.session_state.vector_index.add(np.array(embedding).astype('float32'))
    st.session_state.documents.append(text)

# =========================
# SIDEBAR
# =========================
st.sidebar.title("Rawlings JJ Options")
mode = st.sidebar.radio("Choose Mode:", [
    "Chat", "Transcribe Audio", "TTS", "Execute Python", "OCR / PDF Reader", "Vector Memory Chat"
])

# =========================
# MAIN APP
# =========================
if mode == "Chat":
    st.subheader("Chat with Rawlings JJ")
    user_input = st.text_area("Type your message:")
    if st.button("Send"):
        if user_input.strip():
            with st.spinner("Getting response..."):
                response = chat_with_ai(user_input)
            st.text_area("Rawlings JJ says:", value=response, height=200)

elif mode == "Transcribe Audio":
    st.subheader("Audio Transcription")
    audio_file = st.file_uploader("Upload audio (mp3, wav, m4a)", type=["mp3", "wav", "m4a"])
    if audio_file:
        st.audio(audio_file)
        if st.button("Transcribe Audio"):
            with st.spinner("Transcribing audio..."):
                transcript = transcribe_audio(audio_file)
            st.text_area("Transcript:", value=transcript, height=200)
            if transcript.strip() and st.button("Add Transcript to Memory"):
                add_to_vector_memory(transcript)
                st.success("Transcript added to memory.")

elif mode == "TTS":
    st.subheader("Text-to-Speech (TTS)")
    text_input = st.text_area("Enter text to speak:")
    if st.button("Generate Speech"):
        if text_input.strip():
            try:
                from gtts import gTTS
                tts = gTTS(text=text_input, lang='en')
                audio_bytes = BytesIO()
                tts.write_to_fp(audio_bytes)
                audio_bytes.seek(0)
                st.audio(audio_bytes, format="audio/mp3")
            except Exception as e:
                st.error(f"TTS Error: {e}")

elif mode == "Execute Python":
    st.subheader("Execute Python Code")
    code_input = st.text_area("Enter Python code:")
    if st.button("Run Code"):
        if code_input.strip():
            with st.spinner("Running code..."):
                output = run_python_code(code_input)
            st.text_area("Output:", value=output, height=300)

elif mode == "OCR / PDF Reader":
    st.subheader("OCR and PDF Text Extraction")
    file_input = st.file_uploader("Upload Image or PDF", type=["png", "jpg", "jpeg", "pdf"])
    if file_input:
        if st.button("Extract Text"):
            with st.spinner("Extracting text..."):
                if file_input.type.startswith("image/"):
                    text = ocr_image(file_input)
                elif file_input.type == "application/pdf":
                    text = extract_pdf_text(file_input)
                else:
                    text = "Unsupported file type."
            st.text_area("Extracted Text:", value=text, height=300)
            if text.strip() and st.button("Add Extracted Text to Memory"):
                add_to_vector_memory(text)
                st.success("Text added to memory.")

elif mode == "Vector Memory Chat":
    st.subheader("Chat with Rawlings JJ using Vector Memory")
    user_input = st.text_area("Ask a question or chat with memory:")
    if st.button("Send Memory Chat"):
        if user_input.strip():
            with st.spinner("Getting memory-based response..."):
                response = chat_with_ai(user_input, use_memory=True)
            st.text_area("Rawlings JJ says:", value=response, height=200)
