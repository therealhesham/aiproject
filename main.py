from fastapi import FastAPI, File, UploadFile
from PIL import Image
import pytesseract
import openai
import json
import os
app = FastAPI()

# ضع مفتاح OpenAI هنا
openai.api_key =os.getenv("OPENAI_API_KEY")

# دالة قراءة النصوص من الصورة
def extract_text_from_image(image_path):
    img = Image.open(image_path)
    text = pytesseract.image_to_string(img, lang='ara')  # 'ara' للنص العربي
    return text

# دالة تحليل النصوص واستخراج البيانات
def extract_data(text):
    prompt = f"""
استخرج لي البيانات التالية من النص: الاسم، العمر، البريد، الهاتف
النص: {text}
أرجع النتائج في شكل JSON.
"""
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    try:
        return json.loads(response['choices'][0]['message']['content'])
    except:
        return {"extracted_text": response['choices'][0]['message']['content']}

# نقطة رفع الصورة
@app.post("/upload/")
async def upload_image(file: UploadFile = File(...)):
    path = f"temp_{file.filename}"
    with open(path, "wb") as f:
        f.write(await file.read())
    text = extract_text_from_image(path)
    data = extract_data(text)
    return data
