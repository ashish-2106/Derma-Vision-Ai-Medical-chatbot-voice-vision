import os
import gradio as gr
import sqlite3
from datetime import datetime
from brain_of_the_doctor import encode_image, analyze_image_with_query
from voice_of_the_patient import record_audio, transcribe_with_groq
from voice_of_the_doctor import text_to_speech_with_gtts, text_to_speech_with_elevenlabs

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# Prompt for the AI doctor
system_prompt = """You are an AI medical assistant trained to simulate skin condition assessments from images for educational purposes only.
When shown a skin image, respond as if you are a professional dermatologist.
Begin your response with: 'Based on what I can see, you appear to have...'
Give a short (1–2 sentence) description of the condition.
Then, suggest one specific and plausible over-the-counter or commonly prescribed treatment or medication.
End by reminding the user that this is a simulated diagnosis and they should consult a healthcare professional.
Keep the entire response to a maximum of 3 sentences."""

#  Initialize SQLite DB
def init_db():
    conn = sqlite3.connect("derma_data.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS consultations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            speech_text TEXT,
            doctor_response TEXT,
            audio_path TEXT,
            image_path TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()  # Run at startup

#  Save a consultation to the DB
def save_to_db(speech_text, doctor_response, audio_path, image_path):
    conn = sqlite3.connect("derma_data.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO consultations (timestamp, speech_text, doctor_response, audio_path, image_path)
        VALUES (?, ?, ?, ?, ?)
    """, (
        datetime.now().isoformat(),
        speech_text,
        doctor_response,
        audio_path,
        image_path
    ))
    conn.commit()
    conn.close()

# Main logic
def process_inputs(audio_filepath, image_filepath):
    if not audio_filepath:
        return "No audio provided.", "Please provide an image.", None

    speech_to_text_output = transcribe_with_groq(stt_model="whisper-large-v3", audio_filepath=audio_filepath)

    doctor_response = "No image provided for me to analyze."
    if image_filepath:
        encoded_image = encode_image(image_filepath)
        doctor_response = analyze_image_with_query(
            query=system_prompt + speech_to_text_output, model="meta-llama/llama-4-scout-17b-16e-instruct", encoded_image=encoded_image
        )

    output_audio_path = "final.mp3"
    text_to_speech_with_elevenlabs(input_text=doctor_response, output_filepath=output_audio_path)

    #  Save the session to DB
    save_to_db(
        speech_text=speech_to_text_output,
        doctor_response=doctor_response,
        audio_path=audio_filepath,
        image_path=image_filepath
    )

    return speech_to_text_output, doctor_response, output_audio_path

# ✅ 4. Gradio UI

iface = gr.Interface(
    fn=process_inputs,
    inputs=[
        gr.Audio(sources=["microphone"], type="filepath"),
        gr.Image(type="filepath")
    ],
    outputs=[
        gr.Textbox(label="🗣️ Transcribed Patient Query"),
        gr.Textbox(label="🧠 Doctor's Diagnosis & Advice"),
        gr.Audio("final.mp3")
    ],
    title="🧑‍⚕️ Derma Vision - AI Doctor with Voice and Vision"
)

iface.launch(debug=True)
