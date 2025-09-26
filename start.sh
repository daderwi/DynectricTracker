#!/bin/bash

# Startup-Skript für Dynamic Electric Price Tracker
echo "🚀 Starting Dynamic Electric Price Tracker..."

# Überprüfe Docker Installation
if ! command -v docker &> /dev/null; then
    echo "❌ Docker ist nicht installiert. Bitte installieren Sie Docker zuerst."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose ist nicht installiert. Bitte installieren Sie Docker Compose zuerst."
    exit 1
fi

# Erstelle .env Datei falls nicht vorhanden
if [ ! -f .env ]; then
    echo "📝 Erstelle .env Datei aus Template..."
    cp .env.example .env
    echo "⚠️  Bitte bearbeiten Sie die .env Datei und fügen Sie Ihre API-Schlüssel hinzu:"
    echo "   - ENTSO_E_API_KEY"
    echo "   - TIBBER_API_KEY"
    echo "   Danach das Skript erneut ausführen."
    exit 0
fi

# Lade Umgebungsvariablen
source .env

# Erstelle notwendige Verzeichnisse
mkdir -p database/data
mkdir -p logs

# Starte Services
echo "📦 Starte Docker Container..."
docker-compose up -d

# Warte bis Services bereit sind
echo "⏳ Warte auf Services..."
sleep 30

# Überprüfe Service Status
echo "🔍 Überprüfe Service Status..."

# Backend Health Check
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend ist bereit"
else
    echo "❌ Backend ist nicht verfügbar"
fi

# Frontend Check
if curl -f http://localhost > /dev/null 2>&1; then
    echo "✅ Frontend ist bereit"
else
    echo "❌ Frontend ist nicht verfügbar"
fi

echo ""
echo "🎉 Dynamic Electric Price Tracker ist gestartet!"
echo ""
echo "📱 URLs:"
echo "   Frontend:  http://localhost"
echo "   Backend:   http://localhost:8000"
echo "   API Docs:  http://localhost:8000/docs"
echo ""
echo "📊 Optional (mit --profile monitoring):"
echo "   Grafana:   http://localhost:3000 (admin/admin)"
echo "   Prometheus: http://localhost:9090"
echo ""
echo "🛑 Zum Stoppen: docker-compose down"
echo "📝 Logs anzeigen: docker-compose logs -f"