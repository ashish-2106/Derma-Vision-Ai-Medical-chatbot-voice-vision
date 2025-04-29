import os
import gradio as gr
import sqlite3
import smtplib
import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from datetime import datetime
from brain_of_the_doctor import encode_image, analyze_image_with_query
from voice_of_the_patient import record_audio, transcribe_with_groq
from voice_of_the_doctor import text_to_speech_with_gtts, text_to_speech_with_elevenlabs
from fpdf import FPDF 
from PIL import Image  # For image processing


GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
EMAIL_PASSWORD = os.environ.get("EMAIL_APP_PASSWORD")  # For sending emails
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "ashishjhajharia21@gmail.com")

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
    
    # Get the last inserted ID to return it
    last_id = cursor.lastrowid
    conn.close()
    return last_id

# Function to create PDF transcript with image
def create_pdf_transcript(session_id, speech_text, doctor_response, image_path):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Create PDF file
    class PDF(FPDF):
        def header(self):
            # Logo - can add if needed
            # self.image('logo.png', 10, 8, 33)
            # Set font
            self.set_font('Arial', 'B', 15)
            # Title
            self.cell(0, 10, 'Derma Vision AI - Consultation Report', 0, 1, 'C')
            # Line break
            self.ln(4)
            
    # Initialize PDF
    pdf = PDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Basic info
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 10, f"Consultation ID: {session_id}", 0, 1)
    pdf.cell(0, 10, f"Date: {timestamp}", 0, 1)
    pdf.ln(5)
    
    # Add the skin image if available
    if image_path and os.path.exists(image_path):
        try:
            # Get image dimensions
            with Image.open(image_path) as img:
                width, height = img.size
            
            # Calculate appropriate size for PDF (max width 180, keeping aspect ratio)
            max_width = 180
            max_height = 180
            
            if width > height:
                # Landscape orientation
                img_width = max_width
                img_height = (height / width) * max_width
            else:
                # Portrait orientation
                img_height = max_height
                img_width = (width / height) * max_height
                
            # Add image to PDF
            pdf.set_font('Arial', 'B', 14)
            pdf.cell(0, 10, "Skin Image:", 0, 1)
            pdf.image(image_path, x=None, y=None, w=img_width, h=img_height)
            pdf.ln(10)
        except Exception as e:
            pdf.set_text_color(255, 0, 0)
            pdf.cell(0, 10, f"Error including image: {str(e)}", 0, 1)
            pdf.set_text_color(0, 0, 0)
    
    # Patient Query
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, "Patient Query:", 0, 1)
    pdf.set_font('Arial', '', 12)
    
    # Handle multiline text for patient query
    pdf.multi_cell(0, 10, speech_text)
    pdf.ln(5)
    
    # Doctor's Response
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, "AI Doctor's Response:", 0, 1)
    pdf.set_font('Arial', '', 12)
    
    # Handle multiline text for doctor response
    pdf.multi_cell(0, 10, doctor_response)
    pdf.ln(10)
    
    # Disclaimer footer
    pdf.set_font('Arial', 'I', 10)
    pdf.set_text_color(100, 100, 100)
    pdf.multi_cell(0, 10, "IMPORTANT: This is an AI-generated diagnosis for educational purposes only. Please consult with a healthcare professional for proper medical advice.")
    
    # Save the PDF
    pdf_path = f"session_{session_id}_transcript.pdf"
    pdf.output(pdf_path)
    
    # Also save as JSON for programmatic use if needed
    json_path = f"session_{session_id}.json"
    with open(json_path, "w") as f:
        json.dump({
            "id": session_id,
            "timestamp": timestamp,
            "patient_query": speech_text,
            "doctor_diagnosis": doctor_response,
            "image_path": image_path if image_path else None
        }, f, indent=2)
    
    return pdf_path

# Main logic
def process_inputs(audio_filepath, image_filepath):
    if not audio_filepath:
        return "No audio provided.", "Please provide an image.", None, None, gr.update(visible=False)

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
    session_id = save_to_db(
        speech_text=speech_to_text_output,
        doctor_response=doctor_response,
        audio_path=audio_filepath,
        image_path=image_filepath
    )
    
    # Create PDF transcript file with image
    pdf_path = create_pdf_transcript(session_id, speech_to_text_output, doctor_response, image_filepath)

    return speech_to_text_output, doctor_response, output_audio_path, pdf_path, gr.update(visible=True)

# Function to send email
def send_email(recipient_email, pdf_path, speech_text, doctor_response):
    if not EMAIL_PASSWORD or not recipient_email:
        return "Email configuration missing or no recipient provided."
    
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = recipient_email
        msg['Subject'] = "Derma Vision AI - Consultation Report"
        
        # Email body
        body = f"""
        <html>
        <body>
            <h2>Derma Vision AI - Consultation Report</h2>
            <p><strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <h3>Patient Query:</h3>
            <p>{speech_text}</p>
            <h3>AI Diagnosis (For Review Only):</h3>
            <p>{doctor_response}</p>
            <p><em>This is an AI-generated diagnosis for educational purposes only. Please consult with a healthcare professional.</em></p>
        </body>
        </html>
        """
        msg.attach(MIMEText(body, 'html'))
        
        # Attach the PDF transcript
        with open(pdf_path, "rb") as file:
            attachment = MIMEApplication(file.read(), Name=os.path.basename(pdf_path))
            attachment['Content-Disposition'] = f'attachment; filename="{os.path.basename(pdf_path)}"'
            msg.attach(attachment)
        
        # Send email
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        return f"Email sent successfully to {recipient_email}"
    except Exception as e:
        return f"Failed to send email: {str(e)}"

# ✅ 4. Gradio UI
with gr.Blocks(title="🧑‍⚕ Derma Vision - AI Doctor with Voice and Vision") as iface:
    gr.Markdown("# 🧑‍⚕ Derma Vision - AI Doctor with Voice and Vision")
    
    with gr.Row():
        with gr.Column(scale=1):
            audio_input = gr.Audio(sources=["microphone"], type="filepath", label="Record your question")
            image_input = gr.Image(type="filepath", label="Upload skin image")
            submit_btn = gr.Button("Submit", variant="primary")
            clear_btn = gr.Button("Clear")
        
        with gr.Column(scale=1):
            speech_output = gr.Textbox(label="🗣 Transcribed Patient Query")
            doctor_output = gr.Textbox(label="🧠 Doctor's Diagnosis & Advice")
            audio_output = gr.Audio(label="Doctor's Voice Response")
            
            # Store PDF path but keep it hidden
            pdf_path = gr.Textbox(visible=False)
            
            with gr.Row(visible=False) as share_row:
                # Use a proper downloadable file component for the PDF
                download_output = gr.File(label="📄 Download PDF Report", interactive=False)
                
                with gr.Column():
                    email_input = gr.Textbox(label="Doctor's Email")
                    email_btn = gr.Button("📧 Email to Doctor")
            
            email_status = gr.Textbox(label="Email Status", visible=False)
    
    # Set up event handlers
    submit_btn.click(
        process_inputs,
        inputs=[audio_input, image_input],
        outputs=[speech_output, doctor_output, audio_output, pdf_path, share_row]
    ).then(
        # This function copies the PDF to the download component
        lambda path: path if path else None,
        inputs=[pdf_path],
        outputs=[download_output]
    )
    
    clear_btn.click(
        lambda: (None, None, None, None, gr.update(visible=False), "", None),
        outputs=[audio_input, image_input, speech_output, doctor_output, share_row, email_status, download_output]
    )
    
    email_btn.click(
        send_email,
        inputs=[email_input, pdf_path, speech_output, doctor_output],
        outputs=[email_status]
    ).then(
        lambda: gr.update(visible=True),
        outputs=[email_status]
    )

# Launch the app
iface.launch(debug=True)