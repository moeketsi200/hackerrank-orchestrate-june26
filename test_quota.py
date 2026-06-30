from google import genai
import os
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

models = [
    "gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.0-flash-lite", 
    "gemini-flash-latest", "gemini-flash-lite-latest", "gemini-2.5-flash-lite",
    "gemini-3.5-flash"
]

for m in models:
    try:
        response = client.models.generate_content(
            model=m,
            contents="test"
        )
        print(f"SUCCESS: {m}")
    except Exception as e:
        print(f"FAIL: {m} - {str(e)[:100]}")
