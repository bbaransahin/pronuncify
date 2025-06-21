# Pronuncify

AI assisted pronunciation training app

## System Architecture

This section explains how the app works

### Phonetic Comparision
The user records a sentence and the application transcribes it using the
[faster-whisper](https://github.com/guillaumekln/faster-whisper) `base.en`
model running locally. Word timestamps and confidence scores are returned for
each recognized word. The frontend compares each transcribed word with the
expected sentence. A word is highlighted in green only if it matches the
corresponding word of the sentence **and** its confidence is above the
configurable threshold; otherwise it appears in red.
Punctuation around words is ignored during comparison so that "test" and
"test." are treated as a match.

## Setup

Create a virtual environment and install the dependencies using `pip`:

```bash
pyenv install 3.10.12
pyenv local 3.10.12
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```


The backend uses the [faster-whisper](https://github.com/guillaumekln/faster-whisper)
`base.en` model locally. If you place your `OPENAI_API_KEY` in a `.env` file in
the same directory as `app.py` (typically the project root), the "New Sentence"
button will request practice sentences from the GPT-3.5 API instead of the
fallback list in `static/sentences.txt`.
Sentences are requested in batches of 10 to minimize API usage. The backend
strips numbering or introductions from GPT's reply and retries if fewer than 10
sentences are returned so each line is a normal, punctuated English sentence.
To reduce repetition, a random seed is included in each request and previously
generated sentences are skipped when fetching a new batch.

While a new batch of sentences is loading from GPT, the frontend briefly shows
a spinner so you know it is working.

## Logging

The Flask server writes detailed logs to `app.log` in the project root. Check
this file when debugging the alignment or transcription steps.
