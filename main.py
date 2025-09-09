from fastapi import FastAPI, File, UploadFile
from PIL import Image
import pytesseract
import os
import json
from transformers import pipeline
import re

app = FastAPI()

# Load the text-to-text generation model
nlp = pipeline("text2text-generation", model="google/flan-t5-base")

def clean_text(text):
    """Clean extracted text by removing extra newlines and fixing common OCR errors."""
    text = re.sub(r'\n+', '\n', text.strip())  # Remove multiple newlines
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)  # Replace non-ASCII chars with space (optional, adjust for Arabic)
    return text

def extract_text_from_image(image_path):
    """Extract text from an image using OCR."""
    img = Image.open(image_path)
    text = pytesseract.image_to_string(img, lang="ara+eng")
    return clean_text(text)

def extract_data(text):
    """Convert extracted text to structured JSON using the NLP model."""
    prompt = f"""
    Parse the following text into a structured JSON object suitable for insertion into a database table. Extract all relevant fields such as ReferenceNo, Nationality, FullName, Gender, PassportNo, Religion, IssuingCountry, MaritalStatus, PlaceOfIssue, DateOfBirth, DateIssued, Age, DateExpiry, WeightHeight, and Skills (Cooking, Cleaning, BabySitting). Ensure the output is valid JSON.

    Text:
    {text}
    """
    try:
        result = nlp(prompt, max_length=512, do_sample=False)
        content = result[0]["generated_text"]
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {"error": "Failed to parse generated text as JSON", "generated_text": content}
    except Exception as e:
        return {"error": f"Error processing text: {str(e)}", "input_text": text}

@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    """Handle image upload, extract text, and return structured data."""
    path = f"temp_{file.filename}"
    try:
        with open(path, "wb") as f:
            f.write(await file.read())
        text = extract_text_from_image(path)
        data = extract_data(text)
        return {"text": text, "data": data}
    finally:
        if os.path.exists(path):
            os.remove(path)  # Clean up temporary file