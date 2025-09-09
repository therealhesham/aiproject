from fastapi import FastAPI, File, UploadFile
from PIL import Image
import pytesseract
import os
import re
import json

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
    """Convert extracted text to structured JSON using regex and manual parsing."""
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

    # Extract fields using regex
    ref_match = re.search(r"Reference\s*No\s*(\S+)", text)
    if ref_match: data["ReferenceNo"] = ref_match.group(1)

    nationality_match = re.search(r"Nationality\s*(\S+)", text)
    if nationality_match: data["Nationality"] = nationality_match.group(1)

    name_match = re.search(r"Full\s*Name\s*([A-Z ]+)", text)
    if name_match: data["FullName"] = name_match.group(1).title()

    gender_match = re.search(r"Gender\s*(\S+)", text)
    if gender_match: data["Gender"] = gender_match.group(1)

    passport_match = re.search(r"PassportNo\s*[-]?\s*(\S+)", text)
    if passport_match: data["PassportNo"] = passport_match.group(1)

    religion_match = re.search(r"Religion\s*(\S+)", text)
    if religion_match: data["Religion"] = religion_match.group(1)

    issuing_match = re.search(r"Issuing\s*Country\s*(\S+)", text)
    if issuing_match: data["IssuingCountry"] = issuing_match.group(1)

    marital_match = re.search(r"Martial\s*Status\s*(\S+)", text)
    if marital_match: data["MaritalStatus"] = marital_match.group(1)

    place_match = re.search(r"page of sue\s*([A-Z ]+)", text, re.IGNORECASE)
    if place_match: data["PlaceOfIssue"] = place_match.group(1).title()

    dob_match = re.search(r"Date of Birth\s*(\d{1,2}/\d{1,2}/\d{4})", text)
    if dob_match: data["DateOfBirth"] = dob_match.group(1)

    issued_match = re.search(r"Date Issued\s*(\d{1,2}/\d{1,2}/\d{4})", text)
    if issued_match: data["DateIssued"] = issued_match.group(1)

    age_match = re.search(r"Age\s*(\d+)", text)
    if age_match: data["Age"] = age_match.group(1)

    expiry_match = re.search(r"DateExpiry\s*(\d{1,2}/\d{1,2}/\d{4})", text)
    if expiry_match: data["DateExpiry"] = expiry_match.group(1)

    height_match = re.search(r"Height\s*.*?(\d+cm)", text)
    if height_match: data["Height"] = height_match.group(1)

    weight_match = re.search(r"Weight\s*(\S*)", text)
    if weight_match: data["Weight"] = weight_match.group(1) if weight_match.group(1) else None

    # Skills
    data["Skills"]["Cooking"] = "Yes" if re.search(r"Cooking\s*Yes", text, re.IGNORECASE) else "No"
    data["Skills"]["Cleaning"] = "Yes" if re.search(r"Cleaning\s*Yes", text, re.IGNORECASE) else "No"
    data["Skills"]["BabySitting"] = "Yes" if re.search(r"Baby\s*Sitting\s*Yes", text, re.IGNORECASE) else "No"

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
