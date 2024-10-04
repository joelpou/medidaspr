# Use an official Python image
FROM python:3.9-slim

# Set working directory
WORKDIR /usr/src/app

# Copy the requirements.txt file into the container
COPY ./requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Tesseract OCR
RUN apt-get update && apt-get install -y tesseract-ocr poppler-utils

# Install dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update && apt-get install -y google-chrome-stable \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install ChromeDriver
RUN apt-get update && apt-get install -y \
    unzip \
    # && wget -N https://chromedriver.storage.googleapis.com/114.0.5735.90/chromedriver_linux64.zip \
    # && unzip chromedriver_linux64.zip \
    # && mv chromedriver /usr/local/bin/ \
    # && chmod +x /usr/local/bin/chromedriver \
    # && rm chromedriver_linux64.zip
    && wget -N https://storage.googleapis.com/chrome-for-testing-public/129.0.6668.89/linux64/chrome-linux64.zip \
    && unzip chrome-linux64.zip \
    && mv chrome-linux64 /usr/local/bin/ \
    && chmod +x /usr/local/bin/chrome-linux64 \
    && rm chrome-linux64.zip

COPY . .

# Run the FastAPI server
# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
ENTRYPOINT ["/usr/src/app/entrypoint.sh"]
