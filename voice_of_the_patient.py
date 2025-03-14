import os
import logging
import speech_recognition as sr
from pydub import AudioSegment
from io import BytesIO
from groq import Groq

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
stt_model = "whisper-large-v3"
audio_filepath = "test_audio.mp3"

def record_audio(file_path, timeout=10, phrase_time_limit=5):
    recognizer = sr.Recognizer()

    try:
        with sr.Microphone() as source:
            logging.info("Adjusting for ambient noise...")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            logging.info("Start speaking now...")

            # Record audio
            audio_data = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            logging.info("Recording complete.")

            # Convert to MP3
            wav_data = audio_data.get_wav_data()
            logging.info("Converting to MP3...")
            audio_segment = AudioSegment.from_wav(BytesIO(wav_data))
            audio_segment.export(file_path, format="mp3", bitrate="128k")
            logging.info(f"Audio saved to {file_path}")

            # Verify file exists
            if os.path.exists(file_path):
                logging.info("Audio file successfully created!")
            else:
                logging.error("Failed to save audio file!")

    except Exception as e:
        logging.error(f"An error occurred in record_audio: {e}")

def transcribe_with_groq(stt_model, audio_filepath):
    if not GROQ_API_KEY:
        logging.error("GROQ_API_KEY is missing.")
        return None

    client = Groq(api_key=GROQ_API_KEY)

    try:
        with open(audio_filepath, "rb") as audio_file:
            logging.info("Sending file for transcription...")
            transcription = client.audio.transcriptions.create(
                model=stt_model,
                file=audio_file,
                language="en"
            )
        
        logging.info("Transcription received successfully!")
        print("Transcription:", transcription.text)
        return transcription.text

    except Exception as e:
        logging.error(f"Error in transcription: {e}")
        return None

if __name__ == "__main__":
    logging.info("Starting voice recording...")
    record_audio(audio_filepath)
    
    if os.path.exists(audio_filepath):
        logging.info("Starting transcription...")
        transcript = transcribe_with_groq(stt_model, audio_filepath)
        if transcript:
            logging.info("Transcription completed successfully!")
    else:
        logging.error("Audio file missing, skipping transcription.")
