from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import asyncio
import logging
from sqlalchemy.orm import Session
from ..models import ElectricPrice, Provider, DataCollectionLog
from ..models.schemas import ElectricPriceCreate

logger = logging.getLogger(__name__)


class BaseDataCollector(ABC):
    """Basis-Klasse für alle Datensammler"""
    
    def __init__(self, provider_name: str, api_key: Optional[str] = None):
        self.provider_name = provider_name
        self.api_key = api_key
        self.session = None
    
    @abstractmethod
    async def fetch_prices(self, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """Hole Preisdaten vom API-Endpoint"""
        pass
    
    @abstractmethod
    def parse_price_data(self, raw_data: List[Dict[str, Any]]) -> List[ElectricPriceCreate]:
        """Parse die rohen API-Daten zu ElectricPrice-Objekten"""
        pass
    
    async def collect_and_store(self, db: Session, start_time: datetime, end_time: datetime) -> int:
        """Sammle Daten und speichere sie in der Datenbank"""
        collection_start = datetime.now()
        records_collected = 0
        error_message = None
        status = "success"
        
        try:
            # Provider aus Datenbank holen oder erstellen
            provider = db.query(Provider).filter(Provider.name == self.provider_name).first()
            if not provider:
                logger.warning(f"Provider {self.provider_name} nicht gefunden in der Datenbank")
                return 0
            
            # Daten vom API holen
            raw_data = await self.fetch_prices(start_time, end_time)
            
            if not raw_data:
                logger.warning(f"Keine Daten von {self.provider_name} erhalten")
                status = "partial"
                return 0
            
            # Daten parsen
            price_data = self.parse_price_data(raw_data)
            
            # In Datenbank speichern
            for price_create in price_data:
                price_create.provider_id = provider.id
                
                # Prüfen ob bereits vorhanden
                existing = db.query(ElectricPrice).filter(
                    ElectricPrice.provider_id == provider.id,
                    ElectricPrice.start_time == price_create.start_time,
                    ElectricPrice.end_time == price_create.end_time
                ).first()
                
                if not existing:
                    db_price = ElectricPrice(**price_create.dict())
                    db.add(db_price)
                    records_collected += 1
            
            db.commit()
            logger.info(f"Erfolgreich {records_collected} Preisdatensätze von {self.provider_name} gesammelt")
            
        except Exception as e:
            error_message = str(e)
            status = "error"
            logger.error(f"Fehler beim Sammeln von Daten von {self.provider_name}: {e}")
            db.rollback()
        
        finally:
            # Log-Eintrag erstellen
            execution_time = int((datetime.now() - collection_start).total_seconds() * 1000)
            provider = db.query(Provider).filter(Provider.name == self.provider_name).first()
            
            log_entry = DataCollectionLog(
                provider_id=provider.id if provider else None,
                status=status,
                records_collected=records_collected,
                error_message=error_message,
                execution_time_ms=execution_time
            )
            db.add(log_entry)
            db.commit()
        
        return records_collected
    
    def handle_api_error(self, response_code: int, response_text: str) -> None:
        """Handle API-Fehler"""
        if response_code == 401:
            raise Exception("API-Schlüssel ungültig oder abgelaufen")
        elif response_code == 429:
            raise Exception("API-Rate-Limit erreicht")
        elif response_code >= 500:
            raise Exception(f"Server-Fehler: {response_code}")
        else:
            raise Exception(f"API-Fehler {response_code}: {response_text}")
    
    def calculate_total_price(self, base_price: float, taxes: float = 0.0, grid_fees: float = 0.0) -> float:
        """Berechne Gesamtpreis inkl. Steuern und Gebühren"""
        return round(base_price + taxes + grid_fees, 4)