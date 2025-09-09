from fastapi import FastAPI, File, UploadFile
from PIL import Image
import pytesseract
import os
import json
import ollama
from fastapi.responses import JSONResponse

app = FastAPI()

def clean_text(text):
    """Clean extracted text by removing extra newlines."""
    text = text.strip()
    return text

def extract_text_from_image(image_path):
    """Extract text from an image using OCR."""
    img = Image.open(image_path)
    text = pytesseract.image_to_string(img, lang="ara+eng")
    return clean_text(text)

def process_with_ollama(text):
    """
    Use Ollama with a local LLM to extract structured data from text.
    Returns a JSON object with the same structure as the original data.
    """
    prompt = f"""
    You are an AI model tasked with extracting structured data from text extracted from an image. The text may contain fields like Reference No, Nationality, Full Name, Gender, Passport No, Religion, Issuing Country, Marital Status, Place of Issue, Date of Birth, Date Issued, Age, Date Expiry, Height, Weight, and Skills (Cooking, Cleaning, Baby Sitting). Extract these fields and return a JSON object with the following structure:

    ```json
    {{
        "ReferenceNo": null,
        "Nationality": null,
        "FullName": null,
        "Gender": null,
        "PassportNo": null,
        "Religion": null,
        "IssuingCountry": null,
        "MaritalStatus": null,
        "PlaceOfIssue": null,
        "DateOfBirth": null,
        "DateIssued": null,
        "Age": null,
        "DateExpiry": null,
        "Height": null,
        "Weight": null,
        "Skills": {{
            "Cooking": null,
            "Cleaning": null,
            "BabySitting": null
        }}
    }}
    ```

    For Skills, assign "Yes" or "No" based on whether the text indicates the skill is present (e.g., "Cooking: Yes" or "Cooking: No"). If a field is not found, unclear, or missing, set it to null. Handle dates in the format DD/MM/YYYY. The text may contain noise, typos, or variations in field names (e.g., "Ref No" instead of "Reference No"). The text may include Arabic and English. Use your understanding to extract the most accurate data possible.

    Text to process:
    {text}

    Return only the JSON object as a string, nothing else.
    """

    try:
        # Call Ollama with the local LLM (e.g., LLaMA 3.1 8B)
        response = ollama.generate(
            model="llama3.1:8b",  # Use LLaMA 3.1 8B; adjust if using another model
            prompt=prompt,
            options={"temperature": 0.0}  # Low temperature for structured output
        )

        # Parse the response (Ollama returns a dict with 'response' key)
        data = json.loads(response['response'])

        # Validate the response structure
        expected_keys = {
            "ReferenceNo", "Nationality", "FullName", "Gender", "PassportNo", "Religion",
            "IssuingCountry", "MaritalStatus", "PlaceOfIssue", "DateOfBirth", "DateIssued",
            "Age", "DateExpiry", "Height", "Weight", "Skills"
        }
        if not isinstance(data, dict) or not all(key in data for key in expected_keys):
            raise ValueError("Invalid response structure from Ollama")

        # Validate Skills substructure
        if not isinstance(data["Skills"], dict) or not all(
            key in data["Skills"] for key in ["Cooking", "Cleaning", "BabySitting"]
        ):
            raise ValueError("Invalid Skills structure in Ollama response")

        return data

    except (json.JSONDecodeError, ValueError, Exception) as e:
        # Handle Ollama errors (e.g., model unavailable, invalid JSON, or other issues)
        print(f"Error processing with Ollama: {e}")
        # Fallback to default structure
        return {
            "ReferenceNo": None,
            "Nationality": None,
            "FullName": None,
            "Gender": None,
            "PassportNo": None,
            "Religion": None,
            "IssuingCountry": None,
            "MaritalStatus": None,
            "PlaceOfIssue": None,
            "DateOfBirth": None,
            "DateIssued": None,
            "Age": None,
            "DateExpiry": None,
            "Height": None,
            "Weight": None,
            "Skills": {
                "Cooking": None,
                "Cleaning": None,
                "BabySitting": None
            }
        }

def extract_data(text):
    """Convert extracted text to structured JSON using Ollama."""
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