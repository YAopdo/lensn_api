FROM python:3.11-slim

# 1. System dependencies for Chrome & ChromeDriver
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        wget unzip gnupg curl ca-certificates \
        fonts-liberation libnss3 libxss1 libappindicator3-1 \
        libasound2 libatk-bridge2.0-0 libgtk-3-0 libgbm1 libu2f-udev xdg-utils \
        chromium-driver && \
    rm -rf /var/lib/apt/lists/*

# 2. Install Chrome (stable)
RUN CHROME_VERSION="124.0.6367.91-1" && \
    wget https://dl.google.com/linux/chrome/deb/pool/main/g/google-chrome-stable/google-chrome-stable_${CHROME_VERSION}_amd64.deb && \
    apt install -y ./google-chrome-stable_${CHROME_VERSION}_amd64.deb && \
    rm ./google-chrome-stable_${CHROME_VERSION}_amd64.deb

# 3. Set Chrome binary path (for Selenium)
ENV CHROME_BIN=/usr/bin/google-chrome

# 4. Working dir
WORKDIR /app

# 5. Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copy app source
COPY ./app ./app

# 7. Start FastAPI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
