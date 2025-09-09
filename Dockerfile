# استخدم صورة Python رسمية
FROM python:3.11-slim

# تحديث النظام وتثبيت Tesseract OCR + دعم اللغة العربية
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-ara \
    libtesseract-dev \
    && rm -rf /var/lib/apt/lists/*

# تثبيت مكتبات بايثون المطلوبة
RUN pip install --no-cache-dir fastapi uvicorn pillow pytesseract requests python-dotenv python-multipart

# تعيين مجلد العمل
WORKDIR /app

# نسخ كود المشروع
COPY . .

# فتح البورت
EXPOSE 8000

# تشغيل التطبيق على البورت 8000 (بدل 3030)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
