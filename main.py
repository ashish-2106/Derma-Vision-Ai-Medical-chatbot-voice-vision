from flask import Flask, render_template
import gradio as gr
import threading
from gardio_app import iface  # Make sure this is a Gradio Interface object

app = Flask(__name__, template_folder="templates", static_folder="static")

@app.route("/")
def home():
    return render_template("index.html")  # Firebase login/signup page

@app.route("/app")
def chatbot():
    return render_template("app.html")  # Page to show Gradio chatbot

def run_gradio():
    iface.launch(server_name="0.0.0.0", server_port=7860, share=False)

# Run Gradio on another thread
threading.Thread(target=run_gradio).start()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
