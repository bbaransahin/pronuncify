import os
import tempfile
import logging
import re
import collections
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from pathlib import Path
from faster_whisper import WhisperModel
import openai
import random

load_dotenv(dotenv_path=Path(__file__).with_name(".env"))

# Load the faster-whisper model once at startup
whisper_model = WhisperModel("base.en", device="cpu", compute_type="int8")

app = Flask(__name__)

# Configure logging to file for debugging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("app.log"), logging.StreamHandler()],
)

logger = logging.getLogger(__name__)


class SentenceQueue:
    """Fetch and serve GPT sentences in batches to reduce API calls."""

    def __init__(self, batch_size: int = 10, history_limit: int = 50) -> None:
        self.batch_size = batch_size
        self.queue: list[str] = []
        self.history: collections.deque[str] = collections.deque(maxlen=history_limit)

    def _fetch_batch(self) -> list[str]:
        """Request a batch of sentences from GPT, retrying if few are returned."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OPENAI_API_KEY not set; using fallback sentences")
            return []

        client = openai.OpenAI(api_key=api_key)
        base_prompt = (
            f"Provide {self.batch_size} short English sentences for pronunciation practice. "
            "Avoid rhymes or nonsense. Do not number them or add introductions. "
            "Each sentence must end with a period. Return only the sentences separated by new lines. "
        )

        attempts = 0
        lines: list[str] = []
        while attempts < 3 and len(lines) < self.batch_size:
            attempts += 1
            try:
                prompt = base_prompt + f"Seed: {random.random()}"
                resp = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "system", "content": prompt}],
                    max_tokens=self.batch_size * 25,
                    temperature=0.9,
                    presence_penalty=1.0,
                    frequency_penalty=0.5,
                )
                text = resp.choices[0].message.content
                new_lines = [
                    re.sub(r"^\s*\d+[.)-]?\s*", "", line).strip("- \t")
                    for line in text.splitlines()
                    if line.strip() and re.search(r"[.!?]\s*$", line.strip())
                ]
                unique = [
                    l for l in new_lines if l not in self.history and l not in lines
                ]
                lines.extend(unique)
            except Exception:
                logger.exception("Failed to generate sentences with OpenAI")
                return []

        if len(lines) > self.batch_size:
            lines = lines[: self.batch_size]
        if len(lines) < self.batch_size:
            logger.warning(
                "Expected %d sentences but received %d from OpenAI",
                self.batch_size,
                len(lines),
            )
        self.history.extend(lines)
        logger.info("Generated %d sentences with GPT", len(lines))
        return lines

    def next(self) -> str | None:
        if not self.queue:
            self.queue = self._fetch_batch()
        if self.queue:
            return self.queue.pop(0)
        return None


sentence_queue = SentenceQueue()


def transcribe_audio(audio_path: str):
    """Transcribe the full audio file and return words with probabilities."""
    logger.info("Transcribing with faster-whisper")
    segments, _ = whisper_model.transcribe(
        audio_path,
        word_timestamps=True,
        beam_size=5,
    )

    words = []
    for segment in segments:
        for word in segment.words:
            prob = getattr(word, "probability", None)
            clean = re.sub(r"^[^\w']+|[^\w']+$", "", word.word).lower()
            words.append({"word": word.word, "clean": clean, "prob": prob})

    text = " ".join(w["word"] for w in words)
    return text, words


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/transcribe", methods=["POST"])
def transcribe():
    file = request.files["audio"]  # speech.webm
    logger.info("Received transcription request")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
        file.save(tmp.name)
        text, words = transcribe_audio(tmp.name)
        os.remove(tmp.name)

    logger.info("Transcription completed")

    return jsonify({"text": text, "words": words})


@app.route("/random-sentence")
def random_sentence():
    sentence = sentence_queue.next()
    if not sentence:
        with open("static/sentences.txt", "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
        sentence = random.choice(lines)
    return jsonify({"sentence": sentence})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
