from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./database/electric_prices.db"
    
    # API Keys
    entso_e_api_key: str = ""
    awattar_api_key: str = ""
    tibber_api_key: str = ""
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    
    # App Settings
    secret_key: str = "your-secret-key-change-this"
    api_v1_str: str = "/api/v1"
    project_name: str = "Dynamic Electric Price Tracker"
    
    # CORS
    backend_cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080", 
        "http://localhost:5000"
    ]
    
    # Logging
    log_level: str = "INFO"
    
    # Data Collection
    data_collection_interval: int = 900  # 15 minutes
    retention_days: int = 365
    
    # Smart Home (Future)
    smart_home_enabled: bool = False
    home_assistant_url: str = ""
    home_assistant_token: str = ""
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()