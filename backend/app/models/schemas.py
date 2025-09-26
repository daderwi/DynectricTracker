from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum


class PriceUnit(str, Enum):
    CT_KWH = "ct/kWh"
    EUR_MWH = "€/MWh"


class PriceType(str, Enum):
    SPOT = "spot"
    DAY_AHEAD = "day_ahead"
    INTRADAY = "intraday"


class AlertType(str, Enum):
    BELOW = "below"
    ABOVE = "above"


class DeviceType(str, Enum):
    BATTERY = "battery"
    HEAT_PUMP = "heat_pump"
    EV_CHARGER = "ev_charger"
    SMART_METER = "smart_meter"


# Provider Schemas
class ProviderBase(BaseModel):
    name: str
    display_name: str
    api_endpoint: Optional[str] = None
    country_code: Optional[str] = None
    currency: str = "EUR"
    is_active: bool = True


class ProviderCreate(ProviderBase):
    pass


class Provider(ProviderBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ElectricPrice Schemas
class ElectricPriceBase(BaseModel):
    timestamp: datetime
    start_time: datetime
    end_time: datetime
    price_per_kwh: float
    price_unit: PriceUnit = PriceUnit.CT_KWH
    price_type: PriceType = PriceType.SPOT
    taxes: float = 0.0
    grid_fees: float = 0.0
    total_price: Optional[float] = None
    market_area: Optional[str] = None
    quality_rating: Optional[str] = None
    data_source: Optional[str] = None


class ElectricPriceCreate(ElectricPriceBase):
    provider_id: int
    raw_data: Optional[str] = None


class ElectricPrice(ElectricPriceBase):
    id: int
    provider_id: int
    provider: Provider
    created_at: datetime
    
    class Config:
        from_attributes = True


# PriceAlert Schemas
class PriceAlertBase(BaseModel):
    name: str
    threshold_price: float
    alert_type: AlertType = AlertType.BELOW
    is_active: bool = True
    time_window_hours: int = 24
    min_duration_minutes: int = 60


class PriceAlertCreate(PriceAlertBase):
    provider_id: int


class PriceAlert(PriceAlertBase):
    id: int
    provider_id: int
    provider: Provider
    created_at: datetime
    last_triggered: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# SmartDevice Schemas
class SmartDeviceBase(BaseModel):
    name: str
    device_type: DeviceType
    device_id: Optional[str] = None
    max_power_kw: Optional[float] = None
    capacity_kwh: Optional[float] = None
    efficiency: float = 0.9
    auto_control_enabled: bool = False
    min_price_threshold: Optional[float] = None
    priority: int = 5
    is_active: bool = True


class SmartDeviceCreate(SmartDeviceBase):
    pass


class SmartDevice(SmartDeviceBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# API Response Schemas
class PriceDataResponse(BaseModel):
    prices: List[ElectricPrice]
    count: int
    start_time: datetime
    end_time: datetime
    average_price: float
    min_price: float
    max_price: float


class PriceForecast(BaseModel):
    timestamp: datetime
    predicted_price: float
    confidence: float
    provider_id: int


class ChartDataPoint(BaseModel):
    x: datetime
    y: float
    provider: str
    color: Optional[str] = None


class ChartData(BaseModel):
    datasets: List[dict]
    labels: List[str]
    time_range: str
    unit: str


# WebSocket Message Schemas
class WebSocketMessage(BaseModel):
    type: str  # "price_update", "alert", "status"
    data: dict
    timestamp: datetime = Field(default_factory=datetime.now)


class LivePriceUpdate(BaseModel):
    provider_id: int
    provider_name: str
    current_price: float
    price_change: float
    timestamp: datetime
    next_hour_price: Optional[float] = None