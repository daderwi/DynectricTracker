FROM python:3.11-slim

WORKDIR /app

# System-Abhängigkeiten installieren
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python-Dependencies installieren
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App Code kopieren
COPY . .

# Umgebungsvariablen
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Port freigeben
EXPOSE 8000

# Gesundheitscheck
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# App starten
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]