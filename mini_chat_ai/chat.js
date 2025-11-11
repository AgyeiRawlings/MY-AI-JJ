const chatBox = document.getElementById('chat');
const input = document.getElementById('input');
const button = document.getElementById('send');

button.onclick = async () => {
    const userMessage = input.value.trim();
    if (!userMessage) return; // ignore empty input

    // Append user message
    const msg = document.createElement('p');
    msg.textContent = `You: ${userMessage}`;
    chatBox.appendChild(msg);

    // Clear input
    input.value = '';

    try {
        const response = await fetch('http://127.0.0.1:5000/chat', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ message: userMessage })
        });

        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }

        const data = await response.json();

        // Append AI message
        const aiMsg = document.createElement('p');
        aiMsg.textContent = `AI: ${data.response}`;
        chatBox.appendChild(aiMsg);

        // Auto-scroll to bottom
        chatBox.scrollTop = chatBox.scrollHeight;

    } catch (err) {
        const errorMsg = document.createElement('p');
        errorMsg.textContent = `Error: ${err.message}`;
        errorMsg.style.color = 'red';
        chatBox.appendChild(errorMsg);
        chatBox.scrollTop = chatBox.scrollHeight;
    }
};
