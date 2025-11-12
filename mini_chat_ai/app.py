# app.py
import streamlit as st
import sqlite3
import bcrypt
from datetime import datetime
import logging
from openai import OpenAI
import re
from PIL import Image
import io
import tempfile
import smtplib
from email.mime.text import MIMEText
import streamlit.components.v1 as components
from user_agents import parse
import os
import requests
import pandas as pd

# ----------------------------
# Logging Setup
# ----------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ----------------------------
# Database Setup
# ----------------------------
conn = sqlite3.connect("data.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    email TEXT,
    password_hash TEXT,
    created_at TIMESTAMP
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS analytics (
    username TEXT,
    endpoint TEXT,
    timestamp TIMESTAMP,
    browser TEXT,
    os TEXT,
    device TEXT,
    ip TEXT
)
""")
conn.commit()

# ----------------------------
# OpenAI Client
# ----------------------------
if "OPENAI_API_KEY" not in st.secrets:
    st.error("API key not configured")
    st.stop()
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# ----------------------------
# Utility Functions
# ----------------------------
def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_username(username):
    return username.isalnum() and 3 <= len(username) <= 20

def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt())

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed)

def register_user(username, email, password):
    if not validate_username(username):
        st.error("Invalid username")
        return False
    if not validate_email(email):
        st.error("Invalid email")
        return False
    password_hash = hash_password(password)
    try:
        c.execute(
            "INSERT INTO users (username, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
            (username, email, password_hash, datetime.now())
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        st.error("Username already exists")
        return False

def authenticate(username, password):
    c.execute("SELECT password_hash FROM users WHERE username=?", (username,))
    row = c.fetchone()
    if row and check_password(password, row[0]):
        return True
    return False

def log_call(username, endpoint, browser, os_info, device, ip):
    c.execute(
        "INSERT INTO analytics (username, endpoint, timestamp, browser, os, device, ip) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (username, endpoint, datetime.now(), browser, os_info, device, ip)
    )
    conn.commit()

# ----------------------------
# Email Notification on Login
# ----------------------------
def send_login_alert(username, browser, os_info, device, ip):
    msg = MIMEText(f"""
Alert: Your AI was just accessed.

Username: {username}
Browser: {browser}
OS: {os_info}
Device: {device}
IP Address: {ip}
Timestamp: {datetime.now()}
""")
    msg['Subject'] = "AI Login Alert"
    msg['From'] = "agyeirawlings77@gmail.com"
    msg['To'] = "agyeirawlings77@gmail.com"

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login("agyeirawlings77@gmail.com", st.secrets["email_password"])
            server.send_message(msg)
        logger.info(f"Login alert email sent for user {username}")
    except Exception as e:
        logger.error(f"Failed to send login alert email: {e}")

# ----------------------------
# Device & Browser Info Capture
# ----------------------------
def capture_user_agent():
    if "user_agent" not in st.session_state:
        components.html("""
        <script>
        const ua = navigator.userAgent;
        document.querySelector('body').setAttribute('data-ua', ua);
        </script>
        """, height=0)
        st.session_state.user_agent = "Unknown"

    ua_string = st.session_state.get("user_agent", "Unknown")
    ua = parse(ua_string)
    browser = f"{ua.browser.family} {ua.browser.version_string}"
    os_info = f"{ua.os.family} {ua.os.version_string}"
    device = ua.device.family
    return browser, os_info, device

# ----------------------------
# Get client IP
# ----------------------------
def get_client_ip():
    try:
        ip = requests.get('https://api.ipify.org').text
    except Exception:
        ip = "Unknown"
    return ip

# ----------------------------
# Streamlit UI
# ----------------------------
st.title("Enterprise AI Platform - Unlimited Mode with Vision & Audio")

menu = ["Login", "Register", "Dashboard"]
choice = st.sidebar.selectbox("Menu", menu)

if choice == "Register":
    st.subheader("Create Account")
    username = st.text_input("Username")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Register"):
        if register_user(username, email, password):
            st.success("Registration successful! Please log in.")

elif choice == "Login":
    st.subheader("Login")
    username = st.text_input("Username", key="login_user")
    password = st.text_input("Password", type="password", key="login_pass")
    if st.button("Login"):
        if authenticate(username, password):
            st.success(f"Welcome {username}")
            st.session_state.username = username

            # Capture device info and IP
            browser, os_info, device = capture_user_agent()
            ip = get_client_ip()

            # Log login and send email
            log_call(username, "login", browser, os_info, device, ip)
            send_login_alert(username, browser, os_info, device, ip)

            # ----------------------------
            # AI Query Section
            # ----------------------------
            st.subheader("AI Prompt (Text)")
            prompt = st.text_area("Enter your prompt")

            # ----------------------------
            # File Uploads
            # ----------------------------
            st.subheader("Upload Files / Images / Audio")
            uploaded_file = st.file_uploader("Upload any file", type=None)
            uploaded_image = st.file_uploader("Upload Image", type=['png','jpg','jpeg','bmp','gif'])
            uploaded_audio = st.file_uploader("Upload Audio (WAV, MP3, etc.)", type=['wav','mp3','m4a','flac','ogg','aac'])

            if st.button("Send to AI"):
                try:
                    messages = [{"role": "user", "content": prompt}]

                    # Handle uploaded file
                    if uploaded_file:
                        content = uploaded_file.read()
                        messages.append({
                            "role": "user",
                            "content": f"[FILE CONTENT START]\n{content.decode(errors='ignore')}\n[FILE CONTENT END]"
                        })

                    # Handle uploaded image
                    if uploaded_image:
                        img_bytes = uploaded_image.read()
                        image = Image.open(io.BytesIO(img_bytes))
                        buffered = io.BytesIO()
                        image.save(buffered, format="PNG")
                        buffered.seek(0)
                        response = client.images.analyze(
                            model="gpt-4.1-mini",
                            image=buffered
                        )
                        messages.append({"role": "user", "content": f"[IMAGE ANALYSIS]\n{response['output_text']}"})

                    # Handle uploaded audio
                    if uploaded_audio:
                        with tempfile.NamedTemporaryFile(delete=False) as tmp_audio:
                            tmp_audio.write(uploaded_audio.read())
                            tmp_audio_path = tmp_audio.name
                        try:
                            audio_response = client.audio.transcriptions.create(
                                model="whisper-1",
                                file=open(tmp_audio_path, "rb")
                            )
                            messages.append({"role": "user", "content": f"[AUDIO TRANSCRIPT]\n{audio_response['text']}"})
                        finally:
                            if os.path.exists(tmp_audio_path):
                                os.unlink(tmp_audio_path)

                    # Final AI response
                    chat_response = client.chat.completions.create(
                        model="gpt-4-turbo",
                        messages=messages
                    )
                    answer = chat_response.choices[0].message.content
                    st.write(answer)

                    # Log chat usage
                    log_call(username, "chat", browser, os_info, device, ip)

                except Exception as e:
                    logger.error(f"AI call failed: {e}", exc_info=True)
                    st.error("Failed to get AI response")
        else:
            st.error("Invalid username or password")

elif choice == "Dashboard":
    st.subheader("Recent Logins / Analytics")
    
    st.info("This dashboard shows the recent login activity with device and IP info.")
    
    # Fetch last 20 logins
    c.execute("""
        SELECT username, endpoint, timestamp, browser, os, device, ip 
        FROM analytics 
        ORDER BY timestamp DESC 
        LIMIT 20
    """)
    rows = c.fetchall()
    
    if rows:
        df = pd.DataFrame(rows, columns=["Username", "Endpoint", "Timestamp", "Browser", "OS", "Device", "IP"])
        st.dataframe(df)
    else:
        st.write("No analytics data yet.")
