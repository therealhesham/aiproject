# استخدم صورة Python رسمية
FROM python:3.11-slim

# تحديث النظام وتثبيت Tesseract OCR و دعم اللغة العربية
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-ara \
    libtesseract-dev \
    && rm -rf /var/lib/apt/lists/*

# تثبيت مكتبات بايثون المطلوبة مباشرة
RUN pip install --no-cache-dir fastapi uvicorn pillow pytesseract \
    transformers torch python-multipart

# تعيين مجلد العمل
WORKDIR /app

# نسخ كود المشروع
COPY . .

# فتح البورت
EXPOSE 3030

# تشغيل التطبيق
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3030"]
