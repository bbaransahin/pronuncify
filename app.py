import os
import tempfile
import json
import logging
from flask import Flask, render_template, request, jsonify, abort
from dotenv import load_dotenv
import whisper
import random
from pydub import AudioSegment
from aeneas.executetask import ExecuteTask
from aeneas.task import Task

load_dotenv()

# Load Whisper model once at startup
whisper_model = whisper.load_model("base.en")

app = Flask(__name__)

# Configure logging to file for debugging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ],
)

logger = logging.getLogger(__name__)


def transcribe_by_word(audio_path: str, transcript: str) -> str:
    """Align the audio to the sentence with Aeneas and transcribe each word."""
    logger.info("Starting alignment")
    logger.debug("Transcript: %s", transcript)
    with tempfile.TemporaryDirectory() as workdir:
        wav_path = os.path.join(workdir, "audio.wav")
        AudioSegment.from_file(audio_path).export(wav_path, format="wav")

        txt_path = os.path.join(workdir, "transcript.txt")
        words = [w for w in transcript.strip().split() if w]
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write("\n".join(words))

        task = Task(
            config_string="task_language=eng|is_text_type=plain|os_task_file_format=json"
        )
        task.audio_file_path_absolute = wav_path
        task.text_file_path_absolute = txt_path
        sync_map_path = os.path.join(workdir, "map.json")
        task.sync_map_file_path_absolute = sync_map_path
        ExecuteTask(task).execute()
        task.output_sync_map_file()

        with open(sync_map_path, "r", encoding="utf-8") as f:
            mapping = json.load(f)

        audio = AudioSegment.from_wav(wav_path)
        results = []
        for i, fragment in enumerate(mapping.get("fragments", [])):
            start = float(fragment.get("begin", 0))
            end = float(fragment.get("end", 0))
            logger.debug("Segment %d: %.3f to %.3f", i, start, end)

            start_ms = max(0, int(round(start * 1000)))
            end_ms = max(start_ms + 1, int(round(end * 1000)))

            seg = audio[start_ms:end_ms]

            MIN_MS = 150
            if len(seg) < MIN_MS:
                seg += AudioSegment.silent(duration=MIN_MS - len(seg))
            seg_path = os.path.join(workdir, f"word_{i}.wav")
            seg.export(seg_path, format="wav")
            logger.debug("Transcribing segment %d", i)
            result = whisper_model.transcribe(seg_path, language="en", fp16=False)
            results.append(result.get("text", "").strip())
            logger.debug("Segment %d result: %s", i, result.get("text", "").strip())

        return " ".join(results)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/transcribe", methods=["POST"])
def transcribe():
    file = request.files["audio"]  # speech.webm
    sentence = request.form.get("sentence", "")
    logger.info("Received transcription request")
    logger.debug("Sentence: %s", sentence)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
        file.save(tmp.name)
        try:
            text = transcribe_by_word(tmp.name, sentence)
        except RuntimeError as exc:
            os.remove(tmp.name)
            logger.exception("Alignment failed")
            abort(500, str(exc))
        os.remove(tmp.name)
    logger.info("Transcription completed")

    return jsonify({"text": text})

@app.route("/random-sentence")
def random_sentence():
    with open("static/sentences.txt", "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
    sentence = random.choice(lines)
    return jsonify({"sentence": sentence})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

