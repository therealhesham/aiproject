# استخدم صورة Python خفيفة
FROM python:3.11-slim

# تحديث النظام وتثبيت Tesseract مع دعم اللغة العربية وبعض الأدوات المطلوبة
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-ara \
    libtesseract-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# تعيين مجلد العمل
WORKDIR /app

# نسخ ملفات المشروع
COPY . .

# تثبيت مكتبات بايثون المطلوبة
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn[standard] \
    pillow \
    pytesseract \
    python-multipart \
    openai \
    python-dotenv

# فتح البورت للتطبيق
EXPOSE 3030

# تشغيل التطبيق باستخدام uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3030"]
