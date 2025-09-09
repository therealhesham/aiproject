from fastapi import FastAPI, File, UploadFile
from PIL import Image
import pytesseract
import requests
import os
import json

app = FastAPI()

# عنوان Ollama server (ممكن يتغير لو سيرفر تاني)
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL")


def extract_text_from_image(image_path):
    img = Image.open(image_path)
    text = pytesseract.image_to_string(img, lang="ara")
    return text


def extract_data(text):
    prompt = f"""
استخرج لي البيانات التالية من النص: الاسم، العمر، البريد، الهاتف
النص: {text}
أرجع النتائج في شكل JSON.
"""
    try:
        response = requests.post(
            OLLAMA_API_URL,
            json={
                "model": "mistral",  # أو أي موديل مسحوب عندك
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
            },
            timeout=60,
        )

        if response.status_code != 200:
            return {"error": f"Failed to call Ollama: {response.text}"}

        data = response.json()
        content = data["message"]["content"]

        try:
            return json.loads(content)
        except:
            return {"extracted_text": content}
    except Exception as e:
        return {"error": str(e)}


@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    path = f"temp_{file.filename}"
    with open(path, "wb") as f:
        f.write(await file.read())

    text = extract_text_from_image(path)
    data = extract_data(text)

    os.remove(path)  # حذف الملف المؤقت
    return data
