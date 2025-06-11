# Pronuncify

AI assisted pronunciation training app

## System Architecture

This section explains how the app works

### Phonetic Comparision
Phonetic comparision part first takes the sentence to pronunce and the voice recorded by the user while pronuncing the sentence. Instead of transcribing the full recording at once, the Montreal Forced Aligner is used to obtain timestamps for every word. Each word segment is then fed to Whisper individually (to prevent transcribing words out of context) and compared with the corresponding word in the original sentence.
