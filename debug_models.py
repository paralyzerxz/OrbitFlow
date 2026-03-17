import os
from google import genai #type: ignore
from dotenv import load_dotenv #type: ignore

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=api_key)

print("Listing available models using google.genai:")
try:
    for m in client.models.list():
        print(f"Name: {m.name} (Methods: {m.supported_generation_methods})")
except Exception as e:
    print(f"Error listing models: {e}")

print("\nTesting 'gemini-2.0-flash':")
try:
    response = client.models.generate_content(
        model='gemini-2.0-flash',
        contents="Hello"
    )
    print(f"Success with 'gemini-1.0-flash': {response.text}")
except Exception as e:
    print(f"Error with 'gemini-2.0-flash': {e}")
