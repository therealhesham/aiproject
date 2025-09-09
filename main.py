from fastapi import FastAPI, File, UploadFile
from PIL import Image
import pytesseract
import os
import json
import ollama
from fastapi.responses import JSONResponse

app = FastAPI()

def clean_text(text):
    """Clean extracted text by normalizing whitespace and removing control characters."""
    text = ' '.join(text.split())  # Normalize whitespace
    text = ''.join(c for c in text if c.isprintable())  # Remove non-printable characters
    return text

def extract_text_from_image(image_path):
    """Extract text from an image using OCR."""
    img = Image.open(image_path)
    text = pytesseract.image_to_string(img, lang="ara+eng")
    return clean_text(text)

def normalize_response(response_text):
    """
    Normalize the Ollama response to ensure it’s a valid JSON object.
    Returns a dictionary with extracted key-value pairs or an empty dict on failure.
    """
    try:
        # Try to extract JSON from the response (handle cases with extra text)
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}') + 1
        if start_idx == -1 or end_idx == 0:
            raise ValueError("No valid JSON found in response")

        json_str = response_text[start_idx:end_idx]
        data = json.loads(json_str)

        # Ensure the response is a dictionary
        if not isinstance(data, dict):
            raise ValueError("Response is not a dictionary")

        # Clean and normalize keys/values
        normalized_data = {}
        for key, value in data.items():
            # Remove leading/trailing whitespace from keys and values
            clean_key = key.strip().replace(' ', '_').lower()  # Normalize keys (e.g., "Full Name" -> "full_name")
            clean_value = value.strip() if isinstance(value, str) else value
            # Handle skills values (ensure "Yes" or "No")
            if clean_key in ['cooking', 'cleaning', 'baby_sitting', 'children_care', 'disabled_care', 'washing', 'ironing', 'tutoring']:
                clean_value = "Yes" if str(clean_value).lower() == "yes" else "No" if str(clean_value).lower() == "no" else clean_value
            normalized_data[clean_key] = clean_value

        return normalized_data

    except (json.JSONDecodeError, ValueError) as e:
        print(f"Error normalizing response: {e}")
        return {}

def process_with_ollama(text):
    """
    Use Ollama with a local LLM to extract personal information from text as key-value pairs.
    Returns a JSON object with dynamically extracted fields.
    """
    prompt = f"""
You are an AI tasked with extracting personal information from noisy text extracted from an image via OCR. The text may contain fields like name, age, nationality, passport number, skills, or other personal details, in Arabic, English, or both. Field names may vary (e.g., "Name", "Full Name", "اسم", "الإسم الكامل"), and the text may include OCR errors, typos, or artifacts (e.g., symbols like '|', '©', or random characters).

Your task is to:
1. Identify all key-value pairs related to personal information or skills (e.g., "Name: Ahmed", "Age: 30", "Cooking: Yes").
2. Return them as a JSON object where keys are field names (in English or transliterated from Arabic) and values are the associated data.
3. Do not enforce a specific structure; include only the fields present in the text.
4. Handle OCR noise by ignoring invalid characters and inferring correct field names/values.
5. For skills (e.g., "Cooking", "Cleaning"), assign "Yes" or "No" based on the text.
6. For dates, use the format DD/MM/YYYY if possible.
7. Transliterate Arabic field names to English (e.g., "الإسم الكامل" -> "full_name").
8. Normalize field names to lowercase with underscores (e.g., "Full Name" -> "full_name").
9. Return ONLY the JSON object as a string, with no additional text, comments, or explanations.

Text to process:
{text}
"""

    try:
        # Call Ollama with the local LLM (e.g., LLaMA 3.1 8B)
        response = ollama.generate(
            model="llama3.1:8b",  # Use LLaMA 3.1 8B; adjust if using another model
            prompt=prompt,
            options={"temperature": 0.0}  # Low temperature for structured output
        )

        # Normalize the response to ensure valid JSON
        data = normalize_response(response['response'])
        return data

    except Exception as e:
        # Handle Ollama errors (e.g., model unavailable, invalid JSON, or other issues)
        print(f"Error processing with Ollama: {e}")
        return {}

def extract_data(text):
    """Convert extracted text to dynamic JSON using Ollama."""
    text = clean_text(text)
    data = process_with_ollama(text)
    return data

@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    """Handle image upload, extract text, and return structured data."""
    path = f"temp_{file.filename}"
    try:
        with open(path, "wb") as f:
            f.write(await file.read())

        text = extract_text_from_image(path)
        data = extract_data(text)

        return JSONResponse(content={"text": text, "data": data})

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to process image: {str(e)}"}
        )
    finally:
        if os.path.exists(path):
            os.remove(path)  # Clean up temporary file