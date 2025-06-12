import os
import tempfile
import json
from flask import Flask, render_template, request, jsonify, abort
from dotenv import load_dotenv
import openai
import random
from pydub import AudioSegment
from aeneas.executetask import ExecuteTask
from aeneas.task import Task

load_dotenv()                                # pulls OPENAI_API_KEY
openai.api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)


def transcribe_by_word(audio_path: str, transcript: str) -> str:
    """Align the audio to the sentence with Aeneas and transcribe each word."""
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
            seg = audio[int(start * 1000) : int(end * 1000)]
            seg_path = os.path.join(workdir, f"word_{i}.wav")
            seg.export(seg_path, format="wav")
            with open(seg_path, "rb") as sf:
                resp = openai.audio.transcriptions.create(
                    model="whisper-1",
                    file=sf,
                    language="en",
                )
                results.append(resp.text.strip())

        return " ".join(results)

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

