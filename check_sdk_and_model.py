import os
from google import genai  # type: ignore
from dotenv import load_dotenv  # type: ignore
load_dotenv()
# O segredo: a nova SDK usa Client(), não configure()
client = genai.Client(api_key=os.getenv('GOOGLE_API_KEY'))

# Mude para 2.0 para matar o erro 404 de vez
model_name = 'gemini-2.0-flash' 
print(f"Testing model: {model_name}")

try:
    # Novo método de geração da SDK google-genai
    response = client.models.generate_content(model=model_name, contents="hi")
    print(f"SUCCESS: {response.text}")
except Exception as e:
    print(f"FAIL: {e}")