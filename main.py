from fastapi import FastAPI, File, UploadFile
from PIL import Image
import pytesseract
import os
import json
import ollama
from fastapi.responses import JSONResponse

app = FastAPI()

def clean_text(text):
    """Clean extracted text by removing extra newlines and leading/trailing whitespace."""
    text = ' '.join(text.split())  # Normalize whitespace
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
You are an AI tasked with extracting personal information from text extracted from an image. The text may contain various fields such as name, age, nationality, passport number, or other personal details, in Arabic, English, or both. The fields and their names may vary (e.g., "Name", "Full Name", "اسم", etc.), and the text may include noise, typos, or inconsistent formatting.

Your task is to identify and extract all relevant key-value pairs (e.g., "Name: Ahmed", "Age: 30") and return them as a JSON object. Each key should correspond to the field name (in English or transliterated from Arabic), and the value should be the associated data. For fields indicating skills (e.g., "Cooking: Yes"), assign "Yes" or "No" as the value. If a field is unclear or missing, exclude it from the JSON object. For dates, use the format DD/MM/YYYY if possible. Do not enforce a specific structure; include only the fields present in the text.

Rules:
- Extract all identifiable key-value pairs related to personal information or skills.
- Handle Arabic and English text accurately, accounting for OCR errors or variations.
- Normalize field names to lowercase with underscores (e.g., "Full Name" -> "full_name").
- For skills, use "Yes" or "No" based on the text (e.g., "Cooking: Yes" -> "cooking": "Yes").
- Return ONLY the JSON object as a string, with no additional text, comments, or explanations.

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