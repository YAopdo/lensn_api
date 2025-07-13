FROM python:3.11-slim

# 1. Install Chromium and dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        chromium chromium-driver \
        wget curl unzip gnupg \
        libnss3 libxss1 libappindicator3-1 libasound2 \
        libatk-bridge2.0-0 libgtk-3-0 libgbm1 && \
    rm -rf /var/lib/apt/lists/*

# 2. Set environment so Selenium finds chromium
ENV CHROME_BIN=/usr/bin/chromium
ENV PATH="${PATH}:/usr/bin/chromium"

# 3. Create work directory
WORKDIR /app

# 4. Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy source
COPY ./app ./app

# 6. Start the FastAPI server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
