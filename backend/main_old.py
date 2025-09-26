from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
import socketio
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional
import asyncio
import logging
import os

from app.config import settings
from app.database import engine, get_db
from app.models import Base, Provider, ElectricPrice
from app.models.schemas import *
from app.api import router as api_router

# Logging konfigurieren
logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)

# Datenbank-Tabellen erstellen
Base.metadata.create_all(bind=engine)

# Socket.IO Server konfigurieren
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=settings.backend_cors_origins,
    logger=True,
    engineio_logger=True
)

# FastAPI App
app = FastAPI(
    title=settings.project_name,
    version="1.0.0",
    description="API für dynamische Strompreis-Verfolgung"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Router einbinden
app.include_router(api_router, prefix=settings.api_v1_str)


# Socket.IO Event Handlers
@sio.event
async def connect(sid, environ):
    """Client verbunden"""
    logger.info(f"Client {sid} verbunden")
    await sio.emit('status', {'message': 'Verbindung hergestellt'}, room=sid)


@sio.event
async def disconnect(sid):
    """Client getrennt"""
    logger.info(f"Client {sid} getrennt")


@sio.event
async def subscribe_price_updates(sid, data):
    """Client möchte Preis-Updates für bestimmte Anbieter"""
    provider_ids = data.get('provider_ids', [])
    logger.info(f"Client {sid} abonniert Updates für Provider: {provider_ids}")
    
    # Client zu Räumen hinzufügen
    for provider_id in provider_ids:
        await sio.enter_room(sid, f'provider_{provider_id}')


@sio.event
async def unsubscribe_price_updates(sid, data):
    """Client möchte Preis-Updates abbestellen"""
    provider_ids = data.get('provider_ids', [])
    logger.info(f"Client {sid} beendet Updates für Provider: {provider_ids}")
    
    # Client aus Räumen entfernen
    for provider_id in provider_ids:
        await sio.leave_room(sid, f'provider_{provider_id}')


# Static Files (Frontend) - korrekte Reihenfolge
app.mount("/static", StaticFiles(directory="frontend"), name="static")


# Root Route für Frontend
@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Hauptseite mit Frontend"""
    try:
        with open("frontend/index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse("""
        <html>
        <head><title>Electric Price Tracker</title></head>
        <body>
            <h1>Electric Price Tracker</h1>
            <p>Frontend nicht gefunden. Bitte überprüfen Sie die Frontend-Dateien.</p>
        </body>
        </html>
        """)


# Favicon
@app.get("/favicon.ico")
async def favicon():
    return FileResponse("frontend/favicon.ico", media_type="image/vnd.microsoft.icon")


# Background Task für Live-Updates
async def broadcast_price_updates():
    """Sende regelmäßige Preis-Updates an alle verbundenen Clients"""
    while True:
        try:
            # Demo-Update senden
            await sio.emit('price_update', {
                'type': 'current_prices',
                'data': {
                    'timestamp': datetime.now().isoformat(),
                    'providers': [
                        {
                            'id': 1,
                            'name': 'aWATTar',
                            'current_price': 25.3,
                            'price_change': -2.1
                        },
                        {
                            'id': 2,
                            'name': 'Tibber', 
                            'current_price': 26.8,
                            'price_change': 1.5
                        }
                    ]
                }
            })
            
            # Alle 5 Minuten Updates senden
            await asyncio.sleep(300)
            
        except Exception as e:
            logger.error(f"Fehler beim Senden von Price Updates: {e}")
            await asyncio.sleep(60)


# Startup Event
@app.on_event("startup")
async def startup_event():
    """Beim App-Start"""
    logger.info(f"Starting {settings.project_name}")
    
    # Basis-Provider in DB erstellen falls nicht vorhanden
    db = next(get_db())
    
    providers = [
        {"name": "aWATTar", "display_name": "aWATTar", "country_code": "DE", "currency": "EUR"},
        {"name": "Tibber", "display_name": "Tibber", "country_code": "DE", "currency": "EUR"}, 
        {"name": "ENTSO-E", "display_name": "ENTSO-E", "country_code": "DE", "currency": "EUR"},
    ]
    
    for provider_data in providers:
        existing = db.query(Provider).filter(Provider.name == provider_data["name"]).first()
        if not existing:
            provider = Provider(**provider_data)
            db.add(provider)
    
    db.commit()
    db.close()
    
    # Background Task für Live-Updates starten
    asyncio.create_task(broadcast_price_updates())


# Socket.IO als Sub-App mounten
socket_app = socketio.ASGIApp(sio, other_asgi_app=app, socketio_path='socket.io')