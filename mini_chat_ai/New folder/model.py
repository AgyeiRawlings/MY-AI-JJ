from openai import OpenAI
import os

# -------------- CONFIGURATION --------------
# Put your OpenAI API key here (replace with your own)
os.environ["OPENAI_API_KEY"] = "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"
client = OpenAI()

# -------------- AI RESPONSE FUNCTION --------------
def get_response(prompt: str) -> str:
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are Agyei AI — a smart helpful assistant."},
                {"role": "user", "content": prompt},
            ],
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        return f"[Error] {e}"
