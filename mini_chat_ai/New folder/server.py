from flask import Flask, request, jsonify, render_template_string
from model import get_response

app = Flask(__name__)

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Agyei AI Chat</title>
    <style>
        body { font-family: Arial, sans-serif; background: #f4f4f4; margin: 0; padding: 0; }
        #chatbox { width: 90%; max-width: 700px; margin: 40px auto; background: #fff; padding: 20px;
                   border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
        #messages { height: 400px; overflow-y: auto; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
        .msg { margin: 8px 0; padding: 8px 12px; border-radius: 6px; }
        .user { background: #e1f5fe; text-align: right; }
        .bot { background: #e8f5e9; text-align: left; }
        textarea { width: 100%; height: 80px; margin-top: 10px; border-radius: 6px; padding: 10px; }
        button { padding: 10px 20px; background: #2196f3; color: white; border: none; border-radius: 6px; cursor: pointer; margin-top: 8px; }
        button:hover { background: #1976d2; }
    </style>
</head>
<body>
    <div id="chatbox">
        <h2>💬 Agyei AI</h2>
        <div id="messages"></div>
        <textarea id="input" placeholder="Type your message..."></textarea>
        <button onclick="send()">Send</button>
    </div>

    <script>
        async function send() {
            const msg = document.getElementById('input').value.trim();
            if (!msg) return;
            document.getElementById('messages').innerHTML += `<div class='msg user'><b>You:</b> ${msg}</div>`;
            document.getElementById('input').value = '';

            const res = await fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: msg })
            });
            const data = await res.json();
            document.getElementById('messages').innerHTML += `<div class='msg bot'><b>AI:</b> ${data.reply}</div>`;
            document.getElementById('messages').scrollTop = document.getElementById('messages').scrollHeight;
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_PAGE)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_input = data.get("message", "")
    reply = get_response(user_input)
    return jsonify({"reply": reply})

if __name__ == "__main__":
    print("🚀 Agyei AI running on http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=False)
