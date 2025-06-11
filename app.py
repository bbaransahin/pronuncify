import os, tempfile
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import openai
import random

load_dotenv()                                # pulls OPENAI_API_KEY
openai.api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/transcribe", methods=["POST"])
def transcribe():
    file = request.files["audio"]            # speech.webm
    # Whisper likes real files → use a temp file
    with tempfile.NamedTemporaryFile(delete=True, suffix=".webm") as tmp:
        file.save(tmp.name)
        response = openai.audio.transcriptions.create(
            model="whisper-1",
            file=open(tmp.name, "rb"),
            language="en",
        )
    return jsonify({"text": response.text})

@app.route("/random-sentence")
def random_sentence():
    with open("static/sentences.txt", "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
    sentence = random.choice(lines)
    return jsonify({"sentence": sentence})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

