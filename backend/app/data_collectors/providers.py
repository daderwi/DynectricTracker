import httpx
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
from .base import BaseDataCollector
from ..models.schemas import ElectricPriceCreate, PriceUnit, PriceType
import logging

logger = logging.getLogger(__name__)


class ENTSOECollector(BaseDataCollector):
    """Datensammler für ENTSO-E Transparency Platform"""
    
    def __init__(self, api_key: str):
        super().__init__("ENTSO-E", api_key)
        self.base_url = "https://web-api.tp.entsoe.eu/api"
        
    async def fetch_prices(self, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """Hole Day-Ahead Preise von ENTSO-E"""
        params = {
            'securityToken': self.api_key,
            'documentType': 'A44',  # Day-ahead prices
            'in_Domain': '10Y1001A1001A83F',  # Germany-Luxembourg
            'out_Domain': '10Y1001A1001A83F',
            'periodStart': start_time.strftime('%Y%m%d%H%M'),
            'periodEnd': end_time.strftime('%Y%m%d%H%M')
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(self.base_url, params=params, timeout=30)
                
                if response.status_code != 200:
                    self.handle_api_error(response.status_code, response.text)
                
                # ENTSO-E gibt XML zurück, hier vereinfacht als dict behandelt
                # In Realität würde man XML parsen
                return self._parse_xml_response(response.text)
                
            except httpx.TimeoutException:
                raise Exception("ENTSO-E API Timeout")
    
    def _parse_xml_response(self, xml_content: str) -> List[Dict[str, Any]]:
        """Parse ENTSO-E XML Response - vereinfacht"""
        # Hier würde normalerweise XML geparst werden
        # Für Demo-Zwecke simulieren wir die Daten
        prices = []
        base_time = datetime.now().replace(minute=0, second=0, microsecond=0)
        
        for hour in range(24):
            time_slot = base_time + timedelta(hours=hour)
            prices.append({
                'timestamp': time_slot,
                'price': 50.0 + (hour * 2.5),  # Simulierte Preise
                'currency': 'EUR',
                'unit': 'MWh'
            })
        
        return prices
    
    def parse_price_data(self, raw_data: List[Dict[str, Any]]) -> List[ElectricPriceCreate]:
        """Parse ENTSO-E Daten zu ElectricPrice-Objekten"""
        parsed_prices = []
        
        for item in raw_data:
            timestamp = item['timestamp']
            price_eur_mwh = item['price']
            price_ct_kwh = round(price_eur_mwh / 10, 4)  # EUR/MWh zu ct/kWh
            
            price_obj = ElectricPriceCreate(
                timestamp=timestamp,
                start_time=timestamp,
                end_time=timestamp + timedelta(hours=1),
                price_per_kwh=price_ct_kwh,
                price_unit=PriceUnit.CT_KWH,
                price_type=PriceType.DAY_AHEAD,
                market_area="DE-LU",
                data_source="ENTSO-E",
                raw_data=json.dumps(item),
                total_price=price_ct_kwh
            )
            parsed_prices.append(price_obj)
        
        return parsed_prices


class AwattarCollector(BaseDataCollector):
    """Datensammler für aWATTar API"""
    
    def __init__(self, api_key: str = None):
        super().__init__("aWATTar", api_key)
        self.base_url = "https://api.awattar.de/v1/marketdata"
    
    async def fetch_prices(self, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """Hole Strompreise von aWATTar"""
        params = {
            'start': int(start_time.timestamp() * 1000),
            'end': int(end_time.timestamp() * 1000)
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(self.base_url, params=params, timeout=30)
                
                if response.status_code != 200:
                    self.handle_api_error(response.status_code, response.text)
                
                return response.json().get('data', [])
                
            except httpx.TimeoutException:
                raise Exception("aWATTar API Timeout")
    
    def parse_price_data(self, raw_data: List[Dict[str, Any]]) -> List[ElectricPriceCreate]:
        """Parse aWATTar Daten"""
        parsed_prices = []
        
        for item in raw_data:
            start_timestamp = datetime.fromtimestamp(item['start_timestamp'] / 1000)
            end_timestamp = datetime.fromtimestamp(item['end_timestamp'] / 1000)
            
            # aWATTar gibt Preise in EUR/MWh
            price_eur_mwh = item['marketprice']
            price_ct_kwh = round(price_eur_mwh / 10, 4)
            
            # Zusätzliche Gebühren (Beispielwerte)
            taxes = 0.64  # ct/kWh (EEG-Umlage etc.)
            grid_fees = 7.5  # ct/kWh (Netzentgelt)
            total_price = self.calculate_total_price(price_ct_kwh, taxes, grid_fees)
            
            price_obj = ElectricPriceCreate(
                timestamp=start_timestamp,
                start_time=start_timestamp,
                end_time=end_timestamp,
                price_per_kwh=price_ct_kwh,
                price_unit=PriceUnit.CT_KWH,
                price_type=PriceType.SPOT,
                taxes=taxes,
                grid_fees=grid_fees,
                total_price=total_price,
                market_area="DE",
                data_source="aWATTar",
                raw_data=json.dumps(item)
            )
            parsed_prices.append(price_obj)
        
        return parsed_prices


class TibberCollector(BaseDataCollector):
    """Datensammler für Tibber API"""
    
    def __init__(self, api_key: str):
        super().__init__("Tibber", api_key)
        self.base_url = "https://api.tibber.com/v1-beta/gql"
    
    async def fetch_prices(self, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """Hole Strompreise von Tibber GraphQL API"""
        query = """
        {
          viewer {
            homes {
              currentSubscription {
                priceInfo {
                  current {
                    total
                    startsAt
                  }
                  today {
                    total
                    startsAt
                  }
                  tomorrow {
                    total
                    startsAt
                  }
                }
              }
            }
          }
        }
        """
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.base_url,
                    json={'query': query},
                    headers=headers,
                    timeout=30
                )
                
                if response.status_code != 200:
                    self.handle_api_error(response.status_code, response.text)
                
                data = response.json()
                
                # Extract price data from GraphQL response
                prices = []
                homes = data.get('data', {}).get('viewer', {}).get('homes', [])
                
                for home in homes:
                    price_info = home.get('currentSubscription', {}).get('priceInfo', {})
                    
                    for period in ['today', 'tomorrow']:
                        if period in price_info:
                            prices.extend(price_info[period])
                
                return prices
                
            except httpx.TimeoutException:
                raise Exception("Tibber API Timeout")
    
    def parse_price_data(self, raw_data: List[Dict[str, Any]]) -> List[ElectricPriceCreate]:
        """Parse Tibber Daten"""
        parsed_prices = []
        
        for item in raw_data:
            if not item.get('startsAt') or not item.get('total'):
                continue
                
            start_time = datetime.fromisoformat(item['startsAt'].replace('Z', '+00:00'))
            end_time = start_time + timedelta(hours=1)
            
            # Tibber gibt Gesamtpreis inkl. aller Steuern und Gebühren
            total_price_eur_kwh = item['total']
            price_ct_kwh = round(total_price_eur_kwh * 100, 4)
            
            price_obj = ElectricPriceCreate(
                timestamp=start_time,
                start_time=start_time,
                end_time=end_time,
                price_per_kwh=price_ct_kwh,
                price_unit=PriceUnit.CT_KWH,
                price_type=PriceType.SPOT,
                total_price=price_ct_kwh,
                market_area="DE",
                data_source="Tibber",
                raw_data=json.dumps(item),
                quality_rating="high"
            )
            parsed_prices.append(price_obj)
        
        return parsed_prices