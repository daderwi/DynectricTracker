from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import logging

# Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Electric Price Tracker")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple Routes
@app.get("/")
async def root():
    with open("frontend/index.html", "r") as f:
        return HTMLResponse(f.read())

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/api/v1/providers")
async def providers():
    return [
        {"id": 1, "name": "aWATTar", "display_name": "aWATTar", "country_code": "DE"},
        {"id": 2, "name": "Tibber", "display_name": "Tibber", "country_code": "DE"},
        {"id": 3, "name": "ENTSO-E", "display_name": "ENTSO-E", "country_code": "DE"}
    ]

@app.get("/api/v1/prices/current")
async def current_prices():
    import random
    return [
        {
            "provider": {"id": 1, "name": "aWATTar"},
            "current_price": round(20 + random.random() * 10, 2),
            "total_price": round(25 + random.random() * 10, 2),
            "timestamp": "2025-09-26T18:00:00"
        },
        {
            "provider": {"id": 2, "name": "Tibber"}, 
            "current_price": round(22 + random.random() * 8, 2),
            "total_price": round(27 + random.random() * 8, 2),
            "timestamp": "2025-09-26T18:00:00"
        },
        {
            "provider": {"id": 3, "name": "ENTSO-E"}, 
            "current_price": round(18 + random.random() * 12, 2),
            "total_price": round(23 + random.random() * 12, 2),
            "timestamp": "2025-09-26T18:00:00"
        }
    ]

@app.get("/api/v1/charts/price-comparison")
async def chart_data(
    time_range: str = "24h",
    provider_ids: str = None  # Comma-separated string
):
    import random
    from datetime import datetime, timedelta
    import math
    
    now = datetime.now()
    
    # Zeitraum bestimmen
    if time_range == "24h":
        hours_back = 24
        interval_minutes = 60  # Stündliche Daten
    elif time_range == "7d":
        hours_back = 7 * 24
        interval_minutes = 60  # Stündliche Daten
    elif time_range == "30d":
        hours_back = 30 * 24
        interval_minutes = 24 * 60  # Tägliche Daten
    else:
        hours_back = 24
        interval_minutes = 60
    
    data_points = int(hours_back * 60 / interval_minutes)
    
    # Provider filtern
    all_providers = ["aWATTar", "Tibber", "ENTSO-E"]
    if provider_ids:
        # Parse comma-separated string to list of integers
        try:
            id_list = [int(id.strip()) for id in provider_ids.split(',') if id.strip()]
            provider_map = {1: "aWATTar", 2: "Tibber", 3: "ENTSO-E"}
            selected_providers = [provider_map.get(id) for id in id_list if id in provider_map]
            providers = [p for p in selected_providers if p]
        except (ValueError, AttributeError):
            providers = all_providers
    else:
        providers = all_providers
    
    data = {}
    
    # Sonnenzeiten für Deutschland
    sunrise_hour = 7.0
    sunset_hour = 19.0
    
    # Historische Preis-Trends simulieren
    random.seed(42)  # Für konsistente "historische" Daten
    
    for provider in providers:
        provider_data = []
        
        for i in range(data_points):
            time_point = now - timedelta(minutes=(data_points-1-i) * interval_minutes)
            hour_of_day = time_point.hour + time_point.minute / 60.0
            
            # Basis-Preis je Provider mit historischem Trend
            if provider == "aWATTar":
                base_price = 25 + math.sin(i / 50.0) * 3  # Langzeit-Schwankung
            elif provider == "Tibber":
                base_price = 27 + math.cos(i / 40.0) * 2
            else:  # ENTSO-E
                base_price = 23 + math.sin(i / 60.0) * 4
            
            # Wochentag-Effekt (Wochenende günstiger)
            weekday = time_point.weekday()
            if weekday >= 5:  # Weekend
                base_price *= 0.9
            
            # Sonnenstand-basierte Preismodulation
            if sunrise_hour <= hour_of_day <= sunset_hour:
                sun_angle = math.sin((hour_of_day - sunrise_hour) / (sunset_hour - sunrise_hour) * math.pi)
                solar_factor = 1 + (sun_angle * 0.3)
            else:
                solar_factor = 0.7
            
            # Saisonaler Effekt (Winter teurer)
            month = time_point.month
            if month in [12, 1, 2]:  # Winter
                seasonal_factor = 1.2
            elif month in [6, 7, 8]:  # Sommer
                seasonal_factor = 0.9
            else:
                seasonal_factor = 1.0
            
            price = base_price * solar_factor * seasonal_factor + random.uniform(-2, 2)
            provider_data.append({
                "x": time_point.isoformat(),
                "y": round(max(price, 5), 2)  # Mindestpreis 5 ct/kWh
            })
        
        data[provider] = provider_data
    
    # Sonnenverlauf-Informationen hinzufügen
    sun_data = {
        "sunrise": {
            "time": (now.replace(hour=7, minute=0, second=0, microsecond=0)).isoformat(),
            "hour": 7.0
        },
        "sunset": {
            "time": (now.replace(hour=19, minute=0, second=0, microsecond=0)).isoformat(),
            "hour": 19.0
        },
        "solar_noon": {
            "time": (now.replace(hour=13, minute=0, second=0, microsecond=0)).isoformat(),
            "hour": 13.0
        }
    }
    
    return {
        "datasets": data,
        "sun_data": sun_data,
        "time_range": time_range,
        "unit": "ct/kWh",
        "start_time": (now - timedelta(hours=hours_back)).isoformat(),
        "end_time": now.isoformat(),
        "data_points": data_points
    }

@app.get("/api/v1/stats/daily-average")
async def daily_stats():
    import random
    return [{
        "date": "2025-09-26",
        "average_price": round(25 + random.random() * 5, 2),
        "min_price": round(18 + random.random() * 3, 2),
        "max_price": round(30 + random.random() * 5, 2),
        "data_points": 24
    }]

@app.get("/api/v1/analysis/daily-averages")
async def daily_averages(
    time_range: str = "24h", 
    days_back: int = 7
):
    """Tagesmittelpreise nach Uhrzeit für den gewählten Zeitraum"""
    import random
    from datetime import datetime, timedelta
    import math
    
    # Preismuster über mehrere Tage analysieren
    daily_price_data = {}
    
    # Für jeden Tag in der Vergangenheit
    for day_offset in range(days_back):
        day_prices = []
        
        for hour in range(24):
            # Realistische Preisverteilung über den Tag
            if 6 <= hour <= 8:  # Morgen-Peak
                base_price = 28 + random.uniform(-2, 3)
            elif 11 <= hour <= 15:  # Solar-Peak (höchste Preise)
                base_price = 32 + random.uniform(-1, 5)
            elif 18 <= hour <= 21:  # Abend-Peak
                base_price = 30 + random.uniform(-2, 4)
            elif 22 <= hour <= 5:   # Nacht (niedrigste Preise)
                base_price = 18 + random.uniform(-1, 2)
            else:
                base_price = 24 + random.uniform(-2, 3)
            
            # Wochentag-Effekt
            target_date = datetime.now() - timedelta(days=day_offset)
            if target_date.weekday() >= 5:  # Wochenende
                base_price *= 0.85
            
            # Saisonaler Effekt
            month = target_date.month
            if month in [12, 1, 2]:
                base_price *= 1.15
            elif month in [6, 7, 8]:
                base_price *= 0.95
                
            day_prices.append(max(base_price, 8.0))  # Minimum 8 ct/kWh
        
        daily_price_data[day_offset] = day_prices
    
    # Durchschnitte über alle Tage berechnen
    hourly_averages = []
    for hour in range(24):
        hour_sum = sum(daily_price_data[day][hour] for day in range(days_back))
        hour_avg = hour_sum / days_back
        
        # Min/Max für den Stundenwert ermitteln
        hour_prices = [daily_price_data[day][hour] for day in range(days_back)]
        
        hourly_averages.append({
            "hour": hour,
            "average_price": round(hour_avg, 2),
            "min_price": round(min(hour_prices), 2),
            "max_price": round(max(hour_prices), 2),
            "time_label": f"{hour:02d}:00"
        })
    
    return {
        "hourly_averages": hourly_averages,
        "time_range": time_range,
        "days_analyzed": days_back,
        "unit": "ct/kWh",
        "analysis_period": f"Letzte {days_back} Tage"
    }

@app.get("/api/v1/analysis/energy-sources")
async def energy_sources(time_range: str = "24h"):
    """Energieeinspeisungen nach Quelle über den Tag"""
    import random
    from datetime import datetime, timedelta
    
    # Simulierte Energiequellen-Daten basierend auf realistischen Mustern
    sources_data = []
    
    for hour in range(24):
        # Solar: Nur tagsüber, Peak um Mittag
        if 6 <= hour <= 18:
            solar_factor = max(0, (1 - abs(hour - 12) / 6)) ** 2
            solar = solar_factor * (25000 + random.randint(-3000, 3000))  # MW
        else:
            solar = 0
        
        # Wind: Variabel, oft nachts stärker
        wind_base = 15000 if 20 <= hour or hour <= 6 else 8000
        wind = wind_base + random.randint(-4000, 6000)
        wind = max(0, wind)
        
        # Wasser: Relativ konstant
        hydro = 4000 + random.randint(-500, 500)
        
        # Biomasse: Konstant regelbar
        biomass = 8000 + random.randint(-1000, 1000)
        
        # Fossile Energie (Kohle, Gas): Füllt Lücken auf
        renewable_total = solar + wind + hydro + biomass
        total_demand = 45000 + random.randint(-5000, 8000)  # Simulierte Gesamtnachfrage
        
        fossil = max(0, total_demand - renewable_total)
        nuclear = 8000 + random.randint(-1000, 1000)  # Grundlast
        
        sources_data.append({
            "hour": hour,
            "time_label": f"{hour:02d}:00",
            "solar": round(solar),
            "wind": round(wind), 
            "hydro": round(hydro),
            "biomass": round(biomass),
            "nuclear": round(nuclear),
            "fossil": round(fossil),
            "total_renewable": round(solar + wind + hydro + biomass),
            "total_fossil": round(fossil + nuclear),
            "renewable_percentage": round((solar + wind + hydro + biomass) / max(1, renewable_total + fossil + nuclear) * 100, 1)
        })
    
    return {
        "sources_data": sources_data,
        "time_range": time_range,
        "unit": "MW"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)