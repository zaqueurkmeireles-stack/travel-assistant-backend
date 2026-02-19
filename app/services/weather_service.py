"""
OpenWeather Service - Previsão do tempo
"""

import requests
from app.config import settings
from loguru import logger
from typing import Optional, Dict, List

class WeatherService:
    """Service para integração com OpenWeather API"""
    
    def __init__(self):
        """Inicializa o service"""
        self.api_key = settings.OPENWEATHER_API_KEY
        self.base_url = "https://api.openweathermap.org/data/2.5"
        logger.info("✅ Weather Service inicializado")
    
    def get_current_weather(self, city: str, country_code: str = "") -> Optional[Dict]:
        """Obtém clima atual de uma cidade"""
        try:
            location = f"{city},{country_code}" if country_code else city
            url = f"{self.base_url}/weather"
            params = {
                "q": location,
                "appid": self.api_key,
                "units": "metric",  # Celsius
                "lang": "pt_br"
            }
            
            response = requests.get(url, params=params, timeout=15)
            data = response.json()
            
            if response.status_code == 200:
                return {
                    "temperature": round(data["main"]["temp"]),
                    "feels_like": round(data["main"]["feels_like"]),
                    "humidity": data["main"]["humidity"],
                    "description": data["weather"][0]["description"],
                    "wind_speed": data["wind"]["speed"],
                    "city": data["name"],
                    "country": data["sys"]["country"]
                }
            else:
                logger.warning(f"Erro ao buscar clima: {data.get('message')}")
                return None
                
        except Exception as e:
            logger.error(f"Erro no WeatherService: {e}")
            return None
    
    def get_forecast(self, city: str, days: int = 5) -> Optional[List[Dict]]:
        """Obtém previsão do tempo para os próximos dias"""
        try:
            url = f"{self.base_url}/forecast"
            params = {
                "q": city,
                "appid": self.api_key,
                "units": "metric",
                "lang": "pt_br",
                "cnt": days * 8  # API retorna previsões de 3h em 3h
            }
            
            response = requests.get(url, params=params, timeout=15)
            data = response.json()
            
            if response.status_code == 200:
                forecasts = []
                for item in data["list"][::8]:  # Pegar 1 por dia
                    forecasts.append({
                        "date": item["dt_txt"],
                        "temperature": round(item["main"]["temp"]),
                        "description": item["weather"][0]["description"],
                        "humidity": item["main"]["humidity"]
                    })
                return forecasts
            else:
                logger.warning(f"Erro ao buscar previsão: {data.get('message')}")
                return None
                
        except Exception as e:
            logger.error(f"Erro ao buscar previsão: {e}")
            return None
