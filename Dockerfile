FROM python:3.11-slim

# LibreOffice für docx -> PDF
RUN apt-get update && \
    apt-get install -y --no-install-recommends libreoffice-writer fonts-dejavu && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Render.com/Railway setzen $PORT
ENV PORT=8000
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT}"]
