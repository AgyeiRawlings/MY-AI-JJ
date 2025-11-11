# app.py
import streamlit as st
import openai
from io import BytesIO
from tempfile import NamedTemporaryFile
import subprocess
import os

# =========================
# CONFIGURATION
# =========================
st.set_page_config(page_title="Rawlings JJ - AI Assistant", layout="wide")
st.title("Rawlings JJ - AI Assistant")

# Load OpenAI API key from Streamlit secrets
openai.api_key = st.secrets["OPENAI_API_KEY"]

# =========================
# FUNCTIONS
# =========================

def chat_with_ai(user_input):
    """Chat with OpenAI GPT models using updated API"""
    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": user_input}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {e}"

def transcribe_audio(audio_file):
    """Transcribe audio using OpenAI Whisper API"""
    try:
        # Whisper expects file-like object
        audio_file.seek(0)
        transcript = openai.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
        return transcript.text
    except Exception as e:
        return f"Error: {e}"

def run_python_code(code):
    """Execute Python code safely and return output"""
    try:
        with NamedTemporaryFile(delete=False, suffix=".py") as tmpfile:
            tmpfile.write(code.encode("utf-8"))
            tmpfile.flush()
            result = subprocess.run(
                ["python", tmpfile.name],
                capture_output=True, text=True, timeout=10
            )
        return result.stdout + result.stderr
    except Exception as e:
        return f"Error: {e}"

# =========================
# SIDEBAR
# =========================
st.sidebar.title("Rawlings JJ Options")
mode = st.sidebar.radio("Choose Mode:", ["Chat", "Transcribe Audio", "TTS", "Execute Python"])

# =========================
# MAIN APP
# =========================
if mode == "Chat":
    st.subheader("Chat with Rawlings JJ")
    user_input = st.text_area("Type your message:")
    if st.button("Send"):
        if user_input.strip() != "":
            response = chat_with_ai(user_input)
            st.text_area("Rawlings JJ says:", value=response, height=200)

elif mode == "Transcribe Audio":
    st.subheader("Audio Transcription")
    audio_file = st.file_uploader("Upload audio (mp3, wav, m4a)", type=["mp3","wav","m4a"])
    if audio_file:
        st.audio(audio_file, format="audio/wav")
        if st.button("Transcribe"):
            with st.spinner("Transcribing..."):
                transcript = transcribe_audio(audio_file)
                st.text_area("Transcript:", value=transcript, height=200)

elif mode == "TTS":
    st.subheader("Text-to-Speech (TTS)")
    text_input = st.text_area("Enter text to speak:")
    if st.button("Generate Speech"):
        if text_input.strip() != "":
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
        if code_input.strip() != "":
            output = run_python_code(code_input)
            st.text_area("Output:", value=output, height=300)
