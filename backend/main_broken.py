from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
import logging
import os

from app.config import settings
from app.database import engine, get_db
from app.models import Base, Provider
from app.api import router as api_router

# Logging
logging.basicConfig(level="INFO")
logger = logging.getLogger(__name__)

# DB Setup
Base.metadata.create_all(bind=engine)

# FastAPI App
app = FastAPI(
    title=settings.project_name,
    version="1.0.0",
    description="API für dynamische Strompreis-Verfolgung"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Für Development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routes
app.include_router(api_router, prefix=settings.api_v1_str)

# Static Files
if os.path.exists("frontend"):
    app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Routes
@app.get("/", response_class=HTMLResponse)
async def root():
    try:
        with open("frontend/index.html", "r") as f:
            return HTMLResponse(f.read())
    except:
        return HTMLResponse("<h1>⚡ Electric Price Tracker</h1><p>Loading...</p>")

@app.get("/health")
async def health():
    return {"status": "healthy", "version": "1.0.0"}

@app.on_event("startup")
async def startup():
    logger.info("Starting Electric Price Tracker")
    db = next(get_db())
    try:
        providers = [
            {"name": "aWATTar", "display_name": "aWATTar", "country_code": "DE"},
            {"name": "Tibber", "display_name": "Tibber", "country_code": "DE"},
            {"name": "ENTSO-E", "display_name": "ENTSO-E", "country_code": "DE"},
        ]
        
        for p in providers:
            if not db.query(Provider).filter(Provider.name == p["name"]).first():
                db.add(Provider(**p))
        db.commit()
    finally:
        db.close()