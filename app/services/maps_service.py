"""
Google Maps Service - Geocoding e busca de lugares
"""

import requests
from app.config import settings
from loguru import logger
from typing import Optional, Dict, List

class GoogleMapsService:
    """Service para integração com Google Maps API"""
    
    def __init__(self):
        """Inicializa o service"""
        self.api_key = settings.GOOGLE_MAPS_API_KEY
        self.base_url = "https://maps.googleapis.com/maps/api"
        logger.info("✅ Google Maps Service inicializado")
    
    def geocode(self, address: str) -> Optional[Dict]:
        """Converte endereço em coordenadas"""
        try:
            url = f"{self.base_url}/geocode/json"
            params = {
                "address": address,
                "key": self.api_key
            }
            
            response = requests.get(url, params=params, timeout=15)
            data = response.json()
            
            if data["status"] == "OK":
                location = data["results"][0]["geometry"]["location"]
                return {
                    "lat": location["lat"],
                    "lng": location["lng"],
                    "formatted_address": data["results"][0]["formatted_address"]
                }
            else:
                logger.warning(f"Geocode falhou: {data['status']}")
                return None
                
        except Exception as e:
            logger.error(f"Erro no geocode: {e}")
            return None
    
    def find_nearby_places(self, lat: float, lng: float, place_type: str = "restaurant", radius: int = 1500) -> List[Dict]:
        """Busca lugares próximos"""
        try:
            url = f"{self.base_url}/place/nearbysearch/json"
            params = {
                "location": f"{lat},{lng}",
                "radius": radius,
                "type": place_type,
                "key": self.api_key
            }
            
            response = requests.get(url, params=params, timeout=15)
            data = response.json()
            
            if data["status"] == "OK":
                places = []
                for place in data["results"][:5]:  # Top 5
                    places.append({
                        "name": place.get("name"),
                        "address": place.get("vicinity"),
                        "rating": place.get("rating", "N/A"),
                        "types": place.get("types", [])
                    })
                return places
            else:
                logger.warning(f"Busca de lugares falhou: {data['status']}")
                return []
                
        except Exception as e:
            logger.error(f"Erro ao buscar lugares: {e}")
            return []
    
    def get_directions(self, origin: str, destination: str, mode: str = "driving") -> Optional[Dict]:
        """Obtém direções entre dois pontos"""
        try:
            url = f"{self.base_url}/directions/json"
            params = {
                "origin": origin,
                "destination": destination,
                "mode": mode,
                "key": self.api_key
            }
            
            response = requests.get(url, params=params, timeout=15)
            data = response.json()
            
            if data["status"] == "OK":
                route = data["routes"][0]["legs"][0]
                return {
                    "distance": route["distance"]["text"],
                    "duration": route["duration"]["text"],
                    "start_address": route["start_address"],
                    "end_address": route["end_address"]
                }
            else:
                logger.warning(f"Direções falharam: {data['status']}")
                return None
                
        except Exception as e:
            logger.error(f"Erro ao obter direções: {e}")
            return None
