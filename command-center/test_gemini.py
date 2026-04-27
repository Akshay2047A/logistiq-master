import app
import base64
import os
from dotenv import load_dotenv

load_dotenv("command-center/.env")

model = app.get_gemini_model()
print("Model initialized:", model)

generation_config = {"response_mime_type": "application/json"}
parts = ['{"test": 123}']
response = model.generate_content(parts, generation_config=generation_config)
print(response.text)
