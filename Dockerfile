FROM python:3.11-slim

# 1. Install system dependencies, including Chrome and driver
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        chromium-driver \
        wget \
        unzip \
        curl \
        fonts-liberation \
        libnss3 \
        libxss1 \
        libappindicator3-1 \
        libasound2 \
        libatk-bridge2.0-0 \
        libgtk-3-0 \
        libgbm1 \
        libu2f-udev \
        xdg-utils && \
    rm -rf /var/lib/apt/lists/*

# 2. Download and install latest Chrome manually
RUN CHROME_VERSION="124.0.6367.91-1" && \
    wget https://dl.google.com/linux/chrome/deb/pool/main/g/google-chrome-stable/google-chrome-stable_${CHROME_VERSION}_amd64.deb && \
    apt-get install -y ./google-chrome-stable_${CHROME_VERSION}_amd64.deb && \
    rm google-chrome-stable_${CHROME_VERSION}_amd64.deb

# 3. Set environment variable for Chrome
ENV CHROME_BIN=/usr/bin/google-chrome

# 4. Set working dir
WORKDIR /app

# 5. Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copy your app
COPY ./app ./app

# 7. Run FastAPI server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
