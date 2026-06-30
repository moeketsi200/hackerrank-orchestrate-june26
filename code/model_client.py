import os
import time
from PIL import Image
from google import genai
from google.genai import types
from prompting import ClaimAssessment, SYSTEM_INSTRUCTION

AVAILABLE_MODELS = [
    "gemini-flash-latest",
    "gemini-flash-lite-latest",
    "gemini-2.5-flash-lite",
    "gemini-pro-latest",
    "gemini-2.5-pro",
    "gemini-2.5-flash",
    "gemini-3.5-flash",
    "gemini-2.0-flash-lite",
]
current_model_idx = 0

def init_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_api_key_here":
        raise ValueError("Please set a valid GEMINI_API_KEY in the .env file")
    return genai.Client(api_key=api_key)

def analyze_claim_with_gemini(client: genai.Client, prompt: str, image_paths: list[str]) -> ClaimAssessment:
    global current_model_idx
    contents = [prompt]
    
    for path in image_paths:
        try:
            if os.path.exists(path):
                img = Image.open(path)
                contents.append(img)
            else:
                print(f"Warning: Image file not found {path}")
        except Exception as e:
            print(f"Error loading image {path}: {e}")
            
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_INSTRUCTION,
        response_mime_type="application/json",
        response_schema=ClaimAssessment,
        temperature=0.0,
    )
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            model_name = AVAILABLE_MODELS[current_model_idx]
            response = client.models.generate_content(
                model=model_name,
                contents=contents,
                config=config
            )
            return response.parsed
        except Exception as e:
            error_str = str(e)
            if '429' in error_str and ('quota' in error_str.lower() or 'exhausted' in error_str.lower()):
                if current_model_idx < len(AVAILABLE_MODELS) - 1:
                    print(f"Model {AVAILABLE_MODELS[current_model_idx]} quota exhausted. Switching to {AVAILABLE_MODELS[current_model_idx+1]}...")
                    current_model_idx += 1
                    time.sleep(2)
                    continue
            
            if attempt < max_retries - 1:
                print(f"API Error during generate_content (Attempt {attempt+1}/{max_retries}): {e}")
                time.sleep(15)
            else:
                print(f"API Error during generate_content (Attempt {attempt+1}/{max_retries}): {e}")
                return ClaimAssessment(
                    evidence_standard_met=False,
                    evidence_standard_met_reason=f"API Error: {str(e)}",
                    risk_flags="manual_review_required",
                    issue_type="unknown",
                    object_part="unknown",
                    claim_status="not_enough_information",
                    claim_status_justification="Failed to process image due to API error.",
                    supporting_image_ids="none",
                    valid_image=False,
                    severity="unknown"
                )
