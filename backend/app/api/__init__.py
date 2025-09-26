from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc
from datetime import datetime, timedelta
from typing import List, Optional
import logging

from ..database import get_db
from ..models import Provider, ElectricPrice, PriceAlert, SmartDevice
from ..models.schemas import *

logger = logging.getLogger(__name__)

router = APIRouter()


# Provider Endpoints
@router.get("/providers", response_model=List[Provider])
async def get_providers(
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """Alle verfügbaren Stromanbieter abrufen"""
    query = db.query(Provider)
    if active_only:
        query = query.filter(Provider.is_active == True)
    
    return query.all()


@router.get("/providers/{provider_id}", response_model=Provider)
async def get_provider(provider_id: int, db: Session = Depends(get_db)):
    """Einzelnen Provider abrufen"""
    provider = db.query(Provider).filter(Provider.id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider nicht gefunden")
    return provider


# Strompreis Endpoints
@router.get("/prices", response_model=PriceDataResponse)
async def get_prices(
    provider_ids: Optional[List[int]] = Query(None),
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = Query(100, le=1000),
    db: Session = Depends(get_db)
):
    """Strompreise abrufen mit Filteroptionen"""
    
    # Standardzeitraum: letzte 24 Stunden
    if not start_time:
        start_time = datetime.now() - timedelta(hours=24)
    if not end_time:
        end_time = datetime.now()
    
    # Query aufbauen
    query = db.query(ElectricPrice).filter(
        ElectricPrice.timestamp >= start_time,
        ElectricPrice.timestamp <= end_time
    )
    
    # Provider-Filter
    if provider_ids:
        query = query.filter(ElectricPrice.provider_id.in_(provider_ids))
    
    # Sortierung und Limit
    prices = query.order_by(desc(ElectricPrice.timestamp)).limit(limit).all()
    
    if not prices:
        return PriceDataResponse(
            prices=[],
            count=0,
            start_time=start_time,
            end_time=end_time,
            average_price=0.0,
            min_price=0.0,
            max_price=0.0
        )
    
    # Statistiken berechnen
    price_values = [p.price_per_kwh for p in prices]
    
    return PriceDataResponse(
        prices=prices,
        count=len(prices),
        start_time=start_time,
        end_time=end_time,
        average_price=round(sum(price_values) / len(price_values), 4),
        min_price=min(price_values),
        max_price=max(price_values)
    )


@router.get("/prices/current")
async def get_current_prices(db: Session = Depends(get_db)):
    """Aktuelle Strompreise aller Anbieter"""
    current_time = datetime.now()
    
    # Subquery für die neuesten Preise pro Provider
    subquery = db.query(
        ElectricPrice.provider_id,
        func.max(ElectricPrice.timestamp).label('max_timestamp')
    ).filter(
        ElectricPrice.timestamp <= current_time
    ).group_by(ElectricPrice.provider_id).subquery()
    
    # Join mit Haupttabelle um vollständige Datensätze zu erhalten
    current_prices = db.query(ElectricPrice).join(
        subquery,
        (ElectricPrice.provider_id == subquery.c.provider_id) &
        (ElectricPrice.timestamp == subquery.c.max_timestamp)
    ).all()
    
    result = []
    for price in current_prices:
        result.append({
            "provider": {
                "id": price.provider.id,
                "name": price.provider.display_name
            },
            "current_price": price.price_per_kwh,
            "total_price": price.total_price,
            "timestamp": price.timestamp,
            "price_unit": price.price_unit,
            "market_area": price.market_area
        })
    
    return result


@router.get("/prices/forecast")
async def get_price_forecast(
    provider_id: int,
    hours: int = Query(24, le=72),
    db: Session = Depends(get_db)
):
    """Preisprognose für die nächsten X Stunden"""
    start_time = datetime.now()
    end_time = start_time + timedelta(hours=hours)
    
    forecast_prices = db.query(ElectricPrice).filter(
        ElectricPrice.provider_id == provider_id,
        ElectricPrice.start_time >= start_time,
        ElectricPrice.start_time <= end_time
    ).order_by(asc(ElectricPrice.start_time)).all()
    
    return {
        "provider_id": provider_id,
        "forecast_start": start_time,
        "forecast_end": end_time,
        "prices": forecast_prices
    }


@router.get("/prices/cheapest")
async def get_cheapest_periods(
    duration_hours: int = Query(1, ge=1, le=12),
    lookhead_hours: int = Query(24, le=72),
    provider_ids: Optional[List[int]] = Query(None),
    db: Session = Depends(get_db)
):
    """Günstigste Zeiträume finden"""
    start_time = datetime.now()
    end_time = start_time + timedelta(hours=lookhead_hours)
    
    query = db.query(ElectricPrice).filter(
        ElectricPrice.start_time >= start_time,
        ElectricPrice.start_time <= end_time
    )
    
    if provider_ids:
        query = query.filter(ElectricPrice.provider_id.in_(provider_ids))
    
    all_prices = query.order_by(asc(ElectricPrice.start_time)).all()
    
    # Sliding Window für günstigste Perioden
    cheapest_periods = []
    for i in range(len(all_prices) - duration_hours + 1):
        window_prices = all_prices[i:i + duration_hours]
        if len(window_prices) == duration_hours:
            avg_price = sum(p.price_per_kwh for p in window_prices) / len(window_prices)
            cheapest_periods.append({
                "start_time": window_prices[0].start_time,
                "end_time": window_prices[-1].end_time,
                "average_price": round(avg_price, 4),
                "duration_hours": duration_hours,
                "prices": window_prices
            })
    
    # Nach Durchschnittspreis sortieren
    cheapest_periods.sort(key=lambda x: x["average_price"])
    
    return {
        "duration_hours": duration_hours,
        "periods": cheapest_periods[:10]  # Top 10 günstigste Perioden
    }


# Chart Data Endpoints
@router.get("/charts/price-comparison")
async def get_price_comparison_data(
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    provider_ids: Optional[List[int]] = Query(None),
    db: Session = Depends(get_db)
):
    """Daten für Preisvergleichsdiagramm"""
    
    if not start_time:
        start_time = datetime.now() - timedelta(hours=24)
    if not end_time:
        end_time = datetime.now()
    
    query = db.query(ElectricPrice).filter(
        ElectricPrice.timestamp >= start_time,
        ElectricPrice.timestamp <= end_time
    )
    
    if provider_ids:
        query = query.filter(ElectricPrice.provider_id.in_(provider_ids))
    
    prices = query.order_by(asc(ElectricPrice.timestamp)).all()
    
    # Nach Providern gruppieren
    datasets = {}
    for price in prices:
        provider_name = price.provider.display_name
        if provider_name not in datasets:
            datasets[provider_name] = []
        
        datasets[provider_name].append({
            "x": price.timestamp.isoformat(),
            "y": price.price_per_kwh
        })
    
    return {
        "datasets": datasets,
        "time_range": f"{start_time.isoformat()} - {end_time.isoformat()}",
        "unit": "ct/kWh"
    }


# Statistik Endpoints
@router.get("/stats/daily-average")
async def get_daily_average(
    days: int = Query(30, le=365),
    provider_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Tägliche Durchschnittspreise"""
    start_date = datetime.now().date() - timedelta(days=days)
    
    query = db.query(
        func.date(ElectricPrice.timestamp).label('date'),
        func.avg(ElectricPrice.price_per_kwh).label('avg_price'),
        func.min(ElectricPrice.price_per_kwh).label('min_price'),
        func.max(ElectricPrice.price_per_kwh).label('max_price'),
        func.count(ElectricPrice.id).label('count')
    ).filter(
        func.date(ElectricPrice.timestamp) >= start_date
    )
    
    if provider_id:
        query = query.filter(ElectricPrice.provider_id == provider_id)
    
    daily_stats = query.group_by(func.date(ElectricPrice.timestamp)).all()
    
    return [
        {
            "date": stat.date.isoformat(),
            "average_price": round(stat.avg_price, 4) if stat.avg_price else 0,
            "min_price": stat.min_price,
            "max_price": stat.max_price,
            "data_points": stat.count
        }
        for stat in daily_stats
    ]


# Health Check für Datensammlung
@router.get("/health/data-collection")
async def data_collection_health(db: Session = Depends(get_db)):
    """Status der Datensammlung prüfen"""
    from ..models import DataCollectionLog
    
    # Letzte Logs pro Provider
    latest_logs = db.query(DataCollectionLog).order_by(
        desc(DataCollectionLog.collection_time)
    ).limit(10).all()
    
    provider_status = {}
    for log in latest_logs:
        if log.provider_id not in provider_status:
            provider_status[log.provider_id] = {
                "provider_name": log.provider.display_name if log.provider else "Unknown",
                "last_collection": log.collection_time,
                "status": log.status,
                "records_collected": log.records_collected,
                "error_message": log.error_message
            }
    
    return {
        "overall_status": "healthy" if all(
            status["status"] == "success" 
            for status in provider_status.values()
        ) else "degraded",
        "providers": provider_status
    }