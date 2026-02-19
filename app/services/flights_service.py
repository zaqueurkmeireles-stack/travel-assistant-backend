"""
Flights Service - Monitoramento de voos (AeroDataBox)
"""

import requests
from app.config import settings
from loguru import logger
from typing import Optional, Dict
from datetime import datetime

class FlightsService:
    """Service para monitoramento de voos"""
    
    def __init__(self):
        """Inicializa o service"""
        self.api_key = settings.AERODATABOX_API_KEY
        self.api_host = settings.AERODATABOX_API_HOST
        self.base_url = f"https://{self.api_host}/flights"
        logger.info("✅ Flights Service inicializado")
    
    def get_flight_status(self, flight_number: str, date: str = None) -> Optional[Dict]:
        """Obtém status de um voo"""
        if not self.api_key:
            logger.warning("AeroDataBox API key não configurada")
            return self._mock_flight_status(flight_number)
        
        try:
            if date is None:
                date = datetime.now().strftime("%Y-%m-%d")
            
            url = f"{self.base_url}/number/{flight_number}/{date}"
            headers = {
                "X-RapidAPI-Key": self.api_key,
                "X-RapidAPI-Host": self.api_host
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            data = response.json()
            
            if response.status_code == 200 and len(data) > 0:
                flight = data[0]
                return {
                    "flight_number": flight.get("number"),
                    "airline": flight.get("airline", {}).get("name"),
                    "departure_airport": flight.get("departure", {}).get("airport", {}).get("iata"),
                    "arrival_airport": flight.get("arrival", {}).get("airport", {}).get("iata"),
                    "status": flight.get("status"),
                    "departure_time": flight.get("departure", {}).get("scheduledTime", {}).get("local"),
                    "arrival_time": flight.get("arrival", {}).get("scheduledTime", {}).get("local")
                }
            else:
                logger.warning(f"Voo não encontrado: {flight_number}")
                return None
                
        except Exception as e:
            logger.error(f"Erro ao buscar voo: {e}")
            return self._mock_flight_status(flight_number)
    
    def _mock_flight_status(self, flight_number: str) -> Dict:
        """Retorna dados mock para testes"""
        return {
            "flight_number": flight_number,
            "airline": "LATAM Airlines",
            "departure_airport": "GRU",
            "arrival_airport": "GIG",
            "status": "On Time",
            "departure_time": "2026-04-13T10:00:00",
            "arrival_time": "2026-04-13T11:30:00",
            "note": "Dados simulados"
        }
