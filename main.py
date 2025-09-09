from fastapi import FastAPI, File, UploadFile
from PIL import Image
import pytesseract
import os
import json
import re
from transformers import pipeline

app = FastAPI()

# تحميل موديل توليد النصوص
nlp = pipeline("text2text-generation", model="google/flan-t5-base")


def extract_text_from_image(image_path: str) -> str:
    """استخراج النص من الصورة باستخدام Tesseract OCR"""
    img = Image.open(image_path)
    text = pytesseract.image_to_string(img, lang="ara+eng")
    return text


def regex_fallback(text: str) -> dict:
    """محاولة استخراج البيانات باستخدام Regex في حالة فشل الموديل"""
    data = {}

    name = re.search(r"Full Name\s+([A-Za-z\s]+)", text)
    data["name"] = name.group(1).strip() if name else None

    age = re.search(r"Age\s+(\d+)", text)
    data["age"] = age.group(1) if age else None

    email = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}", text)
    data["email"] = email.group(0) if email else None

    phone = re.search(r"\+?\d[\d\s-]{8,}\d", text)
    data["phone"] = phone.group(0) if phone else None

    passport = re.search(r"PassportNo[-–—]?\s*([A-Z0-9]+)", text)
    data["passport_no"] = passport.group(1) if passport else None

    return data


def extract_data(text: str) -> dict:
    """استخدام الموديل لاستخراج البيانات في شكل JSON"""
    prompt = f"""
    Extract the following information from the text:
    - Full name
    - Age
    - Email
    - Phone
    - Passport number
    
    Text: {text}
    
    Return output as valid JSON with keys: name, age, email, phone, passport_no
    """

    try:
        result = nlp(prompt, max_length=256, do_sample=False)
        content = result[0]["generated_text"]

        try:
            return json.loads(content)  # محاولة تحميل JSON
        except:
            # لو الموديل رجع نص مش JSON، نستخدم regex
            return {"model_output": content, "regex_fallback": regex_fallback(text)}

    except Exception as e:
        return {"error": str(e), "regex_fallback": regex_fallback(text)}


@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    path = f"temp_{file.filename}"
    with open(path, "wb") as f:
        f.write(await file.read())

    text = extract_text_from_image(path)
    data = extract_data(text)

    os.remove(path)  # حذف الملف المؤقت
    return {"text": text, "data": data}
