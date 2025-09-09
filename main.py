from fastapi import FastAPI, File, UploadFile
from PIL import Image
import pytesseract
import openai
import os
import json

app = FastAPI()

# مفتاح OpenAI مخزن في متغير بيئة
openai.api_key = "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"

def extract_text_from_image(image_path):
    img = Image.open(image_path)
    text = pytesseract.image_to_string(img, lang='ara')
    return text

def extract_data(text):
    prompt = f"""
استخرج لي البيانات التالية من النص: الاسم، العمر، البريد، الهاتف
النص: {text}
أرجع النتائج في شكل JSON.
"""
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        content = response.choices[0].message.content
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
