# Use an official Python image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy FastAPI app
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Tesseract OCR
RUN apt-get update && apt-get install -y tesseract-ocr poppler-utils

# Run the FastAPI server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
