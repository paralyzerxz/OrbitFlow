import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
print(f"SDK Version: {genai.__version__}")
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

# O usuario quer exatamente este nome sem models/
model_name = 'gemini-1.5-flash'
print(f"Testing model: {model_name}")

try:
    model = genai.GenerativeModel(model_name)
    print(f"Model object created. Model name used: {model.model_name}")
    response = model.generate_content("hi")
    print("SUCCESS with gemini-1.5-flash")
except Exception as e:
    print(f"FAIL with gemini-1.5-flash: {e}")

# Fallback test para ver se pro funciona
try:
    model2 = genai.GenerativeModel('models/gemini-1.5-flash')
    response2 = model2.generate_content("hi")
    print("SUCCESS with models/gemini-1.5-flash")
except Exception as e:
    print(f"FAIL with models/gemini-1.5-flash: {e}")
