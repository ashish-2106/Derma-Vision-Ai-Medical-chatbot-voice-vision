import os
import base64
from groq import Groq

# Setup Groq API Key
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')

# Convert image to base64
image_path = "acne.jpeg"
with open(image_path, "rb") as image_file:
    encoded_image = base64.b64encode(image_file.read()).decode('utf-8')

# Setup multimodal LLM
client = Groq(api_key=GROQ_API_KEY)

query = "Is there something wrong with my face?"
model = "llama-3.2-90b-vision-preview"

messages = [
    {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": query
            },
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{encoded_image}"}
            }
        ]
    }
]

# Making the API request
chat_completion = client.chat.completions.create(
    messages=messages,
    model=model
)

# Print response
print(chat_completion.choices[0].message.content)
