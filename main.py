from fastapi import FastAPI, File, UploadFile
from PIL import Image
import pytesseract
import os
import re

app = FastAPI()

def clean_text(text):
    """Clean extracted text by removing extra newlines and non-ASCII characters."""
    text = re.sub(r'\n+', '\n', text.strip())  # Remove multiple newlines
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)  # Replace non-ASCII chars with space
    return text

def extract_text_from_image(image_path):
    """Extract text from an image using OCR."""
    img = Image.open(image_path)
    text = pytesseract.image_to_string(img, lang="ara+eng")
    return clean_text(text)

def extract_data(text):
    """Convert extracted text to structured JSON using flexible regex."""
    text = clean_text(text)

    data = {
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

    # Full Name
    name_match = re.search(r"Full\s*Name\s*[\|:]?\s*([A-Z ]+)", text, re.IGNORECASE)
    if name_match:
        data["FullName"] = name_match.group(1).title().strip()

    # Nationality
    nationality_match = re.search(r"Nationality\s*[\|:]?\s*(\S+)", text, re.IGNORECASE)
    if nationality_match:
        data["Nationality"] = nationality_match.group(1).title()

    # Age
    age_match = re.search(r"Age\s*[\|:]?\s*(\d+)", text, re.IGNORECASE)
    if age_match:
        data["Age"] = age_match.group(1)

    # Religion
    religion_match = re.search(r"Religion\s*[\|:]?\s*(\S+)", text, re.IGNORECASE)
    if religion_match:
        data["Religion"] = religion_match.group(1).title()

    # Passport Number
    passport_match = re.search(r"Passport\s*Details.*?Number\s*[\|:]?\s*(\S+)", text, re.IGNORECASE)
    if passport_match:
        data["PassportNo"] = passport_match.group(1)

    # Date Issued
    date_issued_match = re.search(r"Date of Issue\s*[\|:]?\s*(\d{1,2}/\d{1,2}/\d{4})", text, re.IGNORECASE)
    if date_issued_match:
        data["DateIssued"] = date_issued_match.group(1)

    # Date Expiry
    date_expiry_match = re.search(r"Date of Expiry\s*[\|:]?\s*(\d{1,2}/\d{1,2}/\d{4})", text, re.IGNORECASE)
    if date_expiry_match:
        data["DateExpiry"] = date_expiry_match.group(1)

    # Place of Issue
    place_match = re.search(r"Place of Issue\s*[\|:]?\s*([A-Z ]+)", text, re.IGNORECASE)
    if place_match:
        data["PlaceOfIssue"] = place_match.group(1).title().strip()

    # Skills
    data["Skills"]["Cooking"] = "Yes" if re.search(r"Cooking\s*YES", text, re.IGNORECASE) else "No"
    data["Skills"]["Cleaning"] = "Yes" if re.search(r"Cleaning\s*YES", text, re.IGNORECASE) else "No"
    data["Skills"]["BabySitting"] = "Yes" if re.search(r"Baby\s*Sitting\s*YES", text, re.IGNORECASE) else "No"

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

        return {"text": text, "data": data}

    finally:
        if os.path.exists(path):
            os.remove(path)  # Clean up temporary file
