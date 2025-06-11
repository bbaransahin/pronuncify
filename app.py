import os
import os
import tempfile
import subprocess
from flask import Flask, render_template, request, jsonify, abort
from dotenv import load_dotenv
import openai
import random
from pydub import AudioSegment
from praatio import textgrid

load_dotenv()                                # pulls OPENAI_API_KEY
openai.api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)


def transcribe_by_word(audio_path: str, transcript: str) -> str:
    """Align the audio to the sentence with MFA and transcribe each word."""
    with tempfile.TemporaryDirectory() as workdir:
        corpus_dir = os.path.join(workdir, "corpus")
        os.makedirs(corpus_dir, exist_ok=True)

        wav_path = os.path.join(corpus_dir, "audio.wav")
        AudioSegment.from_file(audio_path).export(wav_path, format="wav")

        with open(os.path.join(corpus_dir, "audio.txt"), "w", encoding="utf-8") as f:
            f.write(transcript)

        out_dir = os.path.join(workdir, "aligned")
        try:
            subprocess.run(
                ["mfa", "align", corpus_dir, "english_us_arpa", "english_us_arpa", out_dir, "--clean", "-q"],
                check=True,
            )
        except (FileNotFoundError, subprocess.CalledProcessError) as exc:
            raise RuntimeError(
                "Montreal Forced Aligner failed to run. Is the 'mfa' command installed?"
            ) from exc

        tg_path = os.path.join(out_dir, "audio.TextGrid")
        tg = textgrid.openTextgrid(tg_path, includeEmptyIntervals=False)
        word_tier = tg.getTier("words")
        audio = AudioSegment.from_wav(wav_path)

        words = []
        for i, interval in enumerate(word_tier.entries):
            if not interval.label.strip():
                continue
            seg = audio[int(interval.start * 1000) : int(interval.end * 1000)]
            seg_path = os.path.join(workdir, f"word_{i}.wav")
            seg.export(seg_path, format="wav")
            with open(seg_path, "rb") as sf:
                resp = openai.audio.transcriptions.create(
                    model="whisper-1",
                    file=sf,
                    language="en",
                )
                words.append(resp.text.strip())

        return " ".join(words)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/transcribe", methods=["POST"])
def transcribe():
    file = request.files["audio"]  # speech.webm
    sentence = request.form.get("sentence", "")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
        file.save(tmp.name)
        try:
            text = transcribe_by_word(tmp.name, sentence)
        except RuntimeError as exc:
            os.remove(tmp.name)
            abort(500, str(exc))
        os.remove(tmp.name)

    return jsonify({"text": text})

@app.route("/random-sentence")
def random_sentence():
    with open("static/sentences.txt", "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
    sentence = random.choice(lines)
    return jsonify({"sentence": sentence})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

