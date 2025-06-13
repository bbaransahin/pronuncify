# Pronuncify

AI assisted pronunciation training app

## System Architecture

This section explains how the app works

### Phonetic Comparision
Phonetic comparision part first takes the sentence to pronunce and the voice recorded by the user while pronuncing the sentence. Instead of transcribing the full recording at once, the [Aeneas](https://www.readbeyond.it/aeneas/) aligner is used to obtain timestamps for every word. Each word segment is then fed to Whisper individually (to prevent transcribing words out of context) and compared with the corresponding word in the original sentence. Segments shorter than 150 ms are padded with silence so the Whisper API accepts them.

## Setup

Create a virtual environment and install the dependencies using `pip`:

```bash
pyenv install 3.10.12
pyenv local 3.10.12
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install aeneas
```

Aeneas requires `ffmpeg` and `espeak` to be installed on your system. Refer to
the [Aeneas documentation](https://github.com/readbeyond/aeneas) for
platform-specific installation instructions.

## Logging

The Flask server writes detailed logs to `app.log` in the project root. Check
this file when debugging the alignment or transcription steps.

### OpenAI rate limits

When Whisper API calls are made for each word, requests may hit OpenAI's
per‑second rate limits. The backend inserts a one‑second pause between calls to
avoid 429 errors. If you still see `Too Many Requests` in the log, increase the
delay in `app.py`.
