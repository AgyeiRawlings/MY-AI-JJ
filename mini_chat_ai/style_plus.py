# app_chatgpt_style_plus.py
"""
Rawling JJ AI - ChatGPT-style Streaming Coding Assistant
Features:
- Syntax highlighted code blocks
- Copy-to-clipboard buttons for code
- Sidebar chat history
- Dark/Light mode toggle
- Streaming AI responses
"""

import os
import json
import pickle
import faiss
import threading
from sentence_transformers import SentenceTransformer
from openai import OpenAI
import gradio as gr
import re

# -----------------------------
# CONFIGURATION
# -----------------------------
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "YOUR_OPENAI_API_KEY")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

KNOW
