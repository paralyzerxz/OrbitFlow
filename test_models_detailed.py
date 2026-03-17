import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

print("--- LISTING MODELS ---")
models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
print(f"Detected {len(models)} supporting generateContent.")

for name in models:
    # Skip models known to be deprecated or very old to save time
    if "flash" in name or "pro" in name:
        print(f"\nTesting: {name}")
        try:
            model = genai.GenerativeModel(name)
            response = model.generate_content("hi")
            print(f"SUCCESS: {name}")
            print(f"Response: {response.text[:50]}...")
            # We found it!
            break
        except Exception as e:
            print(f"FAIL {name}: {e}")
