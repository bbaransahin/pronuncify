# Pronuncify

AI assisted pronunciation training app

## System Architecture

This section explains how the app works

### Phonetic Comparision
Phonetic comparision part first takes the sentence to pronunce and the voice recorded by the user while pronuncing the sentence. Instead of transcribing the full recording at once, the Montreal Forced Aligner is used to obtain timestamps for every word. Each word segment is then fed to Whisper individually (to prevent transcribing words out of context) and compared with the corresponding word in the original sentence.

## Setup

Montreal Forced Aligner version 3.1 supports Python 3.10. Newer 3.2 releases
require Python 3.11 or higher and will fail to import on 3.10. You must install
version `3.1.x` and run the application in a Python 3.10 virtual environment. A
quick setup using `pyenv` might look like this:

```bash
pyenv install 3.10.12
pyenv local 3.10.12
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install "montreal-forced-aligner~=3.1"
```

Make sure the `mfa` command is available in your `PATH` after installing the
requirements. Download the pre-built English acoustic model and dictionary from
the [MFA documentation](https://montreal-forced-aligner.readthedocs.io/) and
place them in a directory accessible to the app.

If you encounter an error mentioning `_kalpy` when running `mfa`, double-check
that you installed a 3.1 release of Montreal Forced Aligner and that your
virtual environment uses Python 3.10.
