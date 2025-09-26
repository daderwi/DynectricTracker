import uvicorn
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
import socketio
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import asyncio
import logging
import os

from app.config import settings
from app.database import engine, get_db
from app.models import Base, Provider, ElectricPrice
from app.api import router as api_router

# Logging konfigurieren
logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)

# Datenbank-Tabellen erstellen
Base.metadata.create_all(bind=engine)

# Socket.IO Server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=settings.backend_cors_origins,
    logger=False,  # Weniger verbose logging
    engineio_logger=False
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
    allow_origins=settings.backend_cors_origins + ["*"],  # Für Development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Router
app.include_router(api_router, prefix=settings.api_v1_str)

# Static Files (Frontend)
if os.path.exists("frontend"):
    app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Socket.IO Events
@sio.event
async def connect(sid, environ):
    logger.info(f"Socket.IO Client {sid} connected")
    await sio.emit('status', {'message': 'Verbindung hergestellt'}, room=sid)

@sio.event
async def disconnect(sid):
    logger.info(f"Socket.IO Client {sid} disconnected")

@sio.event
async def subscribe_price_updates(sid, data):
    provider_ids = data.get('provider_ids', [])
    logger.info(f"Client {sid} subscribes to providers: {provider_ids}")
    for provider_id in provider_ids:
        await sio.enter_room(sid, f'provider_{provider_id}')

# Routes
@app.get("/", response_class=HTMLResponse)
async def read_root():
    try:
        with open("frontend/index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse("""
        <!DOCTYPE html>
        <html>
        <head><title>Electric Price Tracker</title></head>
        <body>
            <h1>⚡ Electric Price Tracker</h1>
            <p>Frontend wird geladen...</p>
            <script>
                setTimeout(() => {
                    window.location.reload();
                }, 2000);
            </script>
        </body>
        </html>
        """)

@app.get("/favicon.ico")
async def favicon():
    return {"status": "no favicon"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

# Background task für Demo-Updates
async def price_update_task():
    while True:
        try:
            import random
            await sio.emit('price_update', {
                'type': 'current_prices',
                'timestamp': datetime.now().isoformat(),
                'data': [
                    {
                        'provider_id': 1,
                        'provider_name': 'aWATTar',
                        'current_price': round(20 + random.random() * 10, 2),
                        'price_change': round((random.random() - 0.5) * 4, 2)
                    },
                    {
                        'provider_id': 2,
                        'provider_name': 'Tibber',
                        'current_price': round(22 + random.random() * 8, 2),
                        'price_change': round((random.random() - 0.5) * 3, 2)
                    }
                ]
            })
            await asyncio.sleep(30)  # Update alle 30 Sekunden
        except Exception as e:
            logger.error(f"Error in price update task: {e}")
            await asyncio.sleep(60)

@app.on_event("startup")
async def startup_event():
    logger.info("Starting Electric Price Tracker")
    
    # Provider in DB erstellen
    db = next(get_db())
    try:
        providers = [
            {"name": "aWATTar", "display_name": "aWATTar", "country_code": "DE"},
            {"name": "Tibber", "display_name": "Tibber", "country_code": "DE"},
            {"name": "ENTSO-E", "display_name": "ENTSO-E", "country_code": "DE"},
        ]
        
        for provider_data in providers:
            existing = db.query(Provider).filter(Provider.name == provider_data["name"]).first()
            if not existing:
                provider = Provider(**provider_data)
                db.add(provider)
        
        db.commit()
    except Exception as e:
        logger.error(f"Error creating providers: {e}")
        db.rollback()
    finally:
        db.close()
    
    # Background task starten
    asyncio.create_task(price_update_task())

# Socket.IO App mounten
socket_asgi_app = socketio.ASGIApp(
    sio, 
    other_asgi_app=app, 
    socketio_path='socket.io'
)

if __name__ == "__main__":
    uvicorn.run(socket_asgi_app, host="0.0.0.0", port=8000)