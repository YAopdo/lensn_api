FROM python:3.11-slim

# 1) System deps for Chromium & headless operation
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        chromium chromium-driver gnupg2 && \
    rm -rf /var/lib/apt/lists/*

# 2) Python deps
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3) Copy source
COPY ./app ./app

# 4) Expose static files directory (for the PNGs)
RUN mkdir -p /app/static
ENV STATIC_DIR=/app/static

# 5) Uvicorn entrypoint
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
