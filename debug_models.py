import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

print("Listing available models:")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"Name: {m.name}")
except Exception as e:
    print(f"Error listing models: {e}")

print("\nTesting 'gemini-1.5-flash':")
try:
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content("Hello")
    print(f"Success with 'gemini-1.5-flash': {response.text}")
except Exception as e:
    print(f"Error with 'gemini-1.5-flash': {e}")

print("\nTesting 'models/gemini-1.5-flash':")
try:
    model = genai.GenerativeModel('models/gemini-1.5-flash')
    response = model.generate_content("Hello")
    print(f"Success with 'models/gemini-1.5-flash': {response.text}")
except Exception as e:
    print(f"Error with 'models/gemini-1.5-flash': {e}")
