from fastapi import FastAPI, File, UploadFile
from PIL import Image
import pytesseract
import os
import json
from transformers import pipeline

app = FastAPI()

# تحميل موديل جاهز (ممكن تغيّر mrm8488/t5-base-finetuned-summarize-news بموديل آخر)
nlp = pipeline("text2text-generation", model="google/flan-t5-base")


def extract_text_from_image(image_path):
    img = Image.open(image_path)
    text = pytesseract.image_to_string(img, lang="ara+eng")
    return text


def extract_data(text):
    prompt = f"""
    extract data as json 
    datqa like name or age passport naumber etc
    """
    try:
        result = nlp(prompt, max_length=256, do_sample=False)
        content = result[0]["generated_text"]

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
    return {"text": text, "data": data}
