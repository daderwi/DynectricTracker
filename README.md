# ⚡ Dynamic Electric Price Tracker

Eine umfassende Anwendung zur Verfolgung und Visualisierung dynamischer Strompreise von verschiedenen Anbietern und Strombörsen mit Smart Home Integration.

## 🏗️ Architektur

### Backend
- **Framework**: FastAPI mit SQLAlchemy
- **Datenbank**: PostgreSQL/SQLite
- **Datensammlung**: Automatisierte APIs für Strombörsen (ENTSO-E, EPEX SPOT, etc.)
- **Scheduler**: APScheduler für regelmäßige Datenaktualisierung
- **WebSocket**: Socket.IO für Echtzeit-Updates
- **Smart Home**: Vorbereitung für zukünftige Integration von Energiespeichern

### Frontend
- **Framework**: HTML5 + JavaScript mit Socket.IO
- **Visualisierung**: Chart.js für interaktive Diagramme
- **Echtzeit**: WebSocket-Verbindung für Live-Updates
- **Responsive**: Mobile-optimiert

### Deployment
- **Container**: Docker & Docker Compose
- **Datenbank**: PostgreSQL Container
- **Web**: Nginx als Reverse Proxy
- **Monitoring**: Grafana & Prometheus (optional)

## 🚀 Quick Start

### Mit Docker (Empfohlen)

1. **Repository klonen:**
```bash
git clone <repository-url>
cd dynamic_electric_price_tracker
```

2. **Umgebungsvariablen konfigurieren:**
```bash
cp .env.example .env
# .env Datei mit API-Schlüsseln bearbeiten
```

3. **System starten:**
```bash
# Alle Services starten
docker-compose up -d

# Mit Monitoring (Grafana/Prometheus)
docker-compose --profile monitoring up -d
```

4. **Anwendung öffnen:**
- Frontend: http://localhost
- Backend API: http://localhost/api/v1
- Grafana (optional): http://localhost:3000 (admin/admin)

### Manuelle Installation

1. **Backend installieren:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# oder: venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

2. **Datenbank einrichten:**
```bash
# PostgreSQL starten oder SQLite verwenden
export DATABASE_URL="postgresql://user:password@localhost/electric_prices"
# oder für SQLite: export DATABASE_URL="sqlite:///./database/electric_prices.db"
```

3. **Backend starten:**
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

4. **Frontend bereitstellen:**
```bash
# Nginx konfigurieren oder direkt über Backend unter /static/ verfügbar
```

## 📊 Features

### Aktuelle Features ✅
- **Echtzeit-Strompreisüberwachung** - Live-Updates aller Anbieter
- **Historische Datenanalyse** - Langzeit-Trends und Vergleiche  
- **Multiple Anbieter-Vergleich** - aWATTar, Tibber, ENTSO-E
- **Interaktive Zeitbereichsauswahl** - 24h, 7d, 30d Ansichten
- **WebSocket Live-Updates** - Automatische Preis-Updates
- **Günstigste Zeiträume** - Optimale Lade-/Verbrauchszeiten
- **Responsive Design** - Mobile und Desktop optimiert
- **REST API** - Vollständige API für Drittanbieter-Integration

### Geplante Features 🔄
- **Smart Home Integration** - Home Assistant, openHAB Anbindung
- **Automatische Energiespeicher-Steuerung** - Kostenoptimierte Batterieladung
- **Preisalarme & Benachrichtigungen** - Push/Email bei günstigen Preisen
- **Erweiterte Analytik** - Machine Learning für Preisprognosen
- **Mobile App** - Native iOS/Android Apps

## 📈 Unterstützte Datenquellen

| Anbieter | Status | API Typ | Kosten | Abdeckung |
|----------|--------|---------|---------|-----------|
| **aWATTar** | ✅ Aktiv | REST | Kostenlos | DE, AT |
| **Tibber** | ✅ Aktiv | GraphQL | API Key erforderlich | DE, NO, SE |
| **ENTSO-E** | ✅ Aktiv | REST | API Key erforderlich | Europa |
| **EPEX SPOT** | 🔄 Geplant | REST | Kostenpflichtig | Europa |
| **Nordpool** | 🔄 Geplant | REST | Kostenlos | Nordeuropa |

## 🔧 Konfiguration

### Umgebungsvariablen (.env)

```bash
# Datenbank
DATABASE_URL=postgresql://postgres:password@localhost:5432/electric_prices

# API-Schlüssel
ENTSO_E_API_KEY=your_entso_e_api_key_here
TIBBER_API_KEY=your_tibber_api_key_here

# Redis (für Caching)
REDIS_URL=redis://localhost:6379

# Datensammlung
DATA_COLLECTION_INTERVAL=900  # 15 Minuten
RETENTION_DAYS=365

# Smart Home (Zukunft)
SMART_HOME_ENABLED=false
HOME_ASSISTANT_URL=http://localhost:8123
HOME_ASSISTANT_TOKEN=your_token
```

### API-Schlüssel beantragen

1. **ENTSO-E**: https://transparency.entsoe.eu/
2. **Tibber**: https://developer.tibber.com/
3. **aWATTar**: Kein API-Schlüssel erforderlich

## 🏠 Smart Home Integration (Vorbereitet)

Die Architektur unterstützt bereits:

### Unterstützte Gerätetypen
- **Batteriespeicher** - Automatisierte Ladung bei günstigen Preisen
- **Elektroauto-Ladestationen** - Intelligente Ladevorgänge
- **Wärmepumpen** - Preisoptimierte Heizung/Kühlung
- **Smart Meter** - Verbrauchsmonitoring

### Integration Beispiel
```python
from app.smart_home import BatteryStorage, smart_home_controller

# Batteriespeicher registrieren  
battery = BatteryStorage("battery_1", "Tesla Powerwall", 13.5, 5.0)
smart_home_controller.register_device(battery)

# Automatisierung aktivieren
smart_home_controller.enable_automation(True)
```

## 🚀 Development

### Projekt-Struktur
```
dynamic_electric_price_tracker/
├── backend/                 # FastAPI Backend
│   ├── app/
│   │   ├── api/            # REST API Endpoints  
│   │   ├── models/         # SQLAlchemy Models
│   │   ├── data_collectors/# API Integrations
│   │   ├── services/       # Background Services
│   │   └── smart_home/     # Smart Home Logic
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/               # HTML/JS Frontend
│   ├── index.html
│   ├── app.js
│   └── style.css
├── database/               # DB Scripts
├── docker-compose.yml
└── README.md
```

### Entwicklung starten
```bash
# Backend Development
cd backend
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend Development  
# Frontend wird über Backend unter /static/ bereitgestellt
```

### Tests ausführen
```bash
cd backend
pytest
```

## 📊 Monitoring & Observability

### Grafana Dashboards (Optional)
- Strompreis-Trends
- API-Performance
- System-Metriken
- Alert-Status

### Logs
```bash
# Container Logs anzeigen
docker-compose logs -f backend
docker-compose logs -f collector

# Log-Level anpassen
export LOG_LEVEL=DEBUG
```

## 🔒 Sicherheit

- API-Schlüssel sicher speichern (env vars)
- Reverse Proxy (Nginx) für SSL
- Rate Limiting für APIs
- Input Validation

## 🤝 Contributing

1. Fork das Repository
2. Feature Branch erstellen (`git checkout -b feature/AmazingFeature`)
3. Commit Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to Branch (`git push origin feature/AmazingFeature`)
5. Pull Request öffnen

## 📝 License

Dieses Projekt ist unter der MIT License lizenziert - siehe [LICENSE](LICENSE) Datei.

## 🙋 Support

- **Issues**: GitHub Issues für Bugs und Feature Requests
- **Diskussionen**: GitHub Discussions für Fragen
- **Email**: your-email@example.com

## 🚧 Roadmap

### Version 2.0 (Q1 2024)
- [ ] Smart Home Integration (Home Assistant)
- [ ] Mobile App (React Native)
- [ ] Advanced Analytics Dashboard
- [ ] Price Forecasting ML Model

### Version 3.0 (Q2 2024)  
- [ ] Multi-Market Support (EU-wide)
- [ ] Carbon Footprint Tracking
- [ ] Community Features
- [ ] Commercial API Tier