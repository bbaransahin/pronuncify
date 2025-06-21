# Repository Guide for Pronuncify

This file provides basic orientation for future Codex agents contributing to this project.

## Overview

Pronuncify is a Flask web application that helps users practice their English pronunciation.  It records audio in the browser, transcribes it with [faster-whisper](https://github.com/guillaumekln/faster-whisper), and compares each spoken word with an expected sentence.  Users can request random practice sentences which are either served from a local list or generated through the OpenAI API.

The project layout is small:

- `app.py` – main Flask server and GPT helper logic.
- `templates/` – HTML interface.
- `static/` – fallback sentences.
- `requirements.txt` – Python dependencies.
- `README.md` – setup instructions.

## Formatting Guidelines

- **Python**: run `black -l 88` on any modified `.py` files before committing.
- **HTML / JavaScript**: keep indentation at two spaces.  Use modern ES6 syntax.
- Keep imports grouped in the standard library, third-party, and local order.

## Validation

The repo does not contain a full test suite.  After making changes run:

```bash
python -m py_compile app.py
```

This ensures the application still parses correctly.

## Running the App Locally

1. Create a virtual environment and install dependencies from `requirements.txt`.
2. Run the Flask server:

   ```bash
   python app.py
   ```

Visit `http://localhost:5000` to access the interface.

## Logging

The server writes logs to `app.log` in the project root.  When debugging transcription or alignment issues, inspect this file for details.

