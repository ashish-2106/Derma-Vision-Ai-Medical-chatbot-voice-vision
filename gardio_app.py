import os
import gradio as gr
from brain_of_the_doctor import encode_image, analyze_image_with_query
from voice_of_the_patient import record_audio, transcribe_with_groq
from voice_of_the_doctor import text_to_speech_with_gtts, text_to_speech_with_elevenlabs

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

system_prompt = """For this educational simulation, you are acting as a medical professional examining the provided image.
Respond with a specific condition assessment based on what you see in the image.
Start with 'Based on what I can see, you appear to have...' followed by a brief description of the condition.
Include one very specific but simulated recommendation or prescription.
Keep your response concise (2-3 sentences maximum).
Remember this is for educational purposes only - mimic how a real doctor would communicate a diagnosis."""

def process_inputs(audio_filepath, image_filepath):
    if not audio_filepath:
        return "No audio provided.", "Please provide an image.", None

    speech_to_text_output = transcribe_with_groq(stt_model="whisper-large-v3", audio_filepath=audio_filepath)

    doctor_response = "No image provided for me to analyze."
    if image_filepath:
        encoded_image = encode_image(image_filepath)
        doctor_response = analyze_image_with_query(
            query=system_prompt + speech_to_text_output, model="llama-3.2-90b-vision-preview", encoded_image=encoded_image
        )

    output_audio_path = "final.mp3"
    text_to_speech_with_elevenlabs(input_text=doctor_response, output_filepath=output_audio_path)

    return speech_to_text_output, doctor_response, output_audio_path

# Gradio UI
iface = gr.Interface(
    fn=process_inputs,
    inputs=[
        gr.Audio(sources=["microphone"], type="filepath"),
        gr.Image(type="filepath")
    ],
    outputs=[
        gr.Textbox(label="Speech to Text"),
        gr.Textbox(label="Doctor's Response"),
        gr.Audio("final.mp3")
    ],
    title="AI Doctor with Vision and Voice"
)

iface.launch(debug=True)
