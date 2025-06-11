# Pronuncify

AI assisted pronunciation training app

## System Architecture

This section explains how the app works

### Phonetic Comparision

Phonetic comparision part first takes the sentence to pronunce and the voice recorded by the user while pronuncing the sentence. Then Montreal Forced Aligner aligns the words and whisper model also generates transcriptions for each word separetely (to prevent transcribing words out of context) and it compares the Whisper's transcriptions with the corresponding words in the original sentence. 
