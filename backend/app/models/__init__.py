from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base


class Provider(Base):
    """Stromanbieter und Datenquellen"""
    __tablename__ = "providers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)  # z.B. "Awattar", "ENTSO-E", "Tibber"
    display_name = Column(String(100), nullable=False)  # Anzeigename
    api_endpoint = Column(String(500))  # API URL
    country_code = Column(String(2), index=True)  # DE, AT, etc.
    currency = Column(String(3), default="EUR")  # EUR, USD, etc.
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    prices = relationship("ElectricPrice", back_populates="provider")


class ElectricPrice(Base):
    """Haupttabelle für Strompreise"""
    __tablename__ = "electric_prices"
    
    id = Column(Integer, primary_key=True, index=True)
    provider_id = Column(Integer, ForeignKey("providers.id"), nullable=False)
    
    # Zeitdaten
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    start_time = Column(DateTime(timezone=True), nullable=False)  # Gültigkeitsbeginn
    end_time = Column(DateTime(timezone=True), nullable=False)    # Gültigkeitsende
    
    # Preisdaten
    price_per_kwh = Column(Float, nullable=False)  # Preis in Cent/kWh oder Euro/MWh
    price_unit = Column(String(10), default="ct/kWh")  # "ct/kWh", "€/MWh"
    price_type = Column(String(20), default="spot")  # "spot", "day_ahead", "intraday"
    
    # Zusätzliche Gebühren und Steuern
    taxes = Column(Float, default=0.0)  # Steuern in ct/kWh
    grid_fees = Column(Float, default=0.0)  # Netzentgelte
    total_price = Column(Float)  # Gesamtpreis inkl. aller Abgaben
    
    # Metadaten
    market_area = Column(String(20))  # z.B. "DE-LU", "AT"
    quality_rating = Column(String(10))  # "high", "medium", "low"
    data_source = Column(String(50))  # Original-Datenquelle
    raw_data = Column(Text)  # Original JSON response für Debugging
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    provider = relationship("Provider", back_populates="prices")
    
    # Indexes for performance
    __table_args__ = (
        Index('ix_provider_timestamp', 'provider_id', 'timestamp'),
        Index('ix_timestamp_price', 'timestamp', 'price_per_kwh'),
        Index('ix_start_end_time', 'start_time', 'end_time'),
    )


class PriceAlert(Base):
    """Preisalarme für günstige Stromzeiten"""
    __tablename__ = "price_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    provider_id = Column(Integer, ForeignKey("providers.id"))
    
    # Alert-Konfiguration
    threshold_price = Column(Float, nullable=False)  # Schwellenwert in ct/kWh
    alert_type = Column(String(20), default="below")  # "below", "above"
    is_active = Column(Boolean, default=True)
    
    # Zeitfenster
    time_window_hours = Column(Integer, default=24)  # In den nächsten X Stunden
    min_duration_minutes = Column(Integer, default=60)  # Mindestdauer der günstigen Phase
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_triggered = Column(DateTime(timezone=True))
    
    # Relationship
    provider = relationship("Provider")


class SmartDevice(Base):
    """Smart Home Geräte für zukünftige Integration"""
    __tablename__ = "smart_devices"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    device_type = Column(String(50))  # "battery", "heat_pump", "ev_charger"
    device_id = Column(String(100))  # Home Assistant Entity ID
    
    # Gerätespezifikationen
    max_power_kw = Column(Float)  # Maximale Leistung in kW
    capacity_kwh = Column(Float)  # Kapazität (für Batterien/EVs)
    efficiency = Column(Float, default=0.9)  # Wirkungsgrad 0-1
    
    # Steuerungseinstellungen
    auto_control_enabled = Column(Boolean, default=False)
    min_price_threshold = Column(Float)  # Maximaler Preis für automatisches Laden
    priority = Column(Integer, default=5)  # Priorität 1-10
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class DataCollectionLog(Base):
    """Log für Datensammlungsvorgänge"""
    __tablename__ = "data_collection_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    provider_id = Column(Integer, ForeignKey("providers.id"))
    
    collection_time = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String(20))  # "success", "error", "partial"
    records_collected = Column(Integer, default=0)
    error_message = Column(Text)
    execution_time_ms = Column(Integer)  # Ausführungszeit in Millisekunden
    
    # Relationship
    provider = relationship("Provider")