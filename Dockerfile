FROM python:3.11-slim

# LibreOffice für docx -> PDF
RUN apt-get update && \
    apt-get install -y --no-install-recommends libreoffice-writer fonts-dejavu fontconfig && \
    rm -rf /var/lib/apt/lists/*

# Vorlagen-Schriften (Source Sans Pro + Open Sans) — ohne die schneidet
# LibreOffice die Überschriften ab und nimmt Ersatz-Serifenschrift
COPY fonts/ /usr/share/fonts/truetype/custom/
RUN fc-cache -f

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Render.com/Railway setzen $PORT
ENV PORT=8000
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT}"]
