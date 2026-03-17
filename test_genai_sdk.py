import os
from google import genai  # type: ignore
from dotenv import load_dotenv  # type: ignore

load_dotenv()
# Criando o cliente novo que o VS Code agora reconhece
client = genai.Client(api_key=os.getenv('GOOGLE_API_KEY'))

print("--- LISTING MODELS ---")
try:
    # Método atualizado para listar os modelos
    for m in client.models.list():
        print(f"Name: {m.name}")
except Exception as e:
    print(f"Error: {e}")

print("\nTesting 'gemini-2.0-flash':")
try:
    # Testando o modelo que realmente funciona
    response = client.models.generate_content(
        model='gemini-2.0-flash', 
        contents="hi"
    )
    print(f"SUCCESS: {response.text}")
except Exception as e:
    print(f"FAIL: {e}")
