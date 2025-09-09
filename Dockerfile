# Use official Python slim image
FROM python:3.11-slim

# Update system and install Tesseract OCR with Arabic language support and curl
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-ara \
    libtesseract-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama server and pull LLaMA 3.1 8B model
RUN ollama serve & \
    sleep 10 && \
    ollama pull llama3.1:8b

# Install Python dependencies
RUN pip install --no-cache-dir fastapi uvicorn pillow pytesseract python-multipart ollama

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Expose port
EXPOSE 3030

# Start Ollama server in the background and run the FastAPI application
CMD ["/bin/bash", "-c", "ollama serve & sleep 15 && uvicorn main:app --host 0.0.0.0 --port 3030"]