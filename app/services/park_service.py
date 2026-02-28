"""
Park Service - Integração com a API ThemeParks.wiki para tempos de espera.
"""

import requests
from typing import List, Dict, Any, Optional
from loguru import logger

class ParkService:
    """Service para buscar dados em tempo real de parques temáticos"""
    
    BASE_URL = "https://api.themeparks.wiki/v1"
    
    # Dados dos Parques para Geofencing
    PARK_DATA = {
        "europa_park": {
            "id": "85e3b542-af91-4f8a-8d28-445868a7c8fd",
            "name": "Europa Park",
            "lat": 48.2662,
            "lng": 7.7220
        },
        "disneyland_paris": {
            "id": "62f02611-ead5-46f0-93a0-388f55331526",
            "name": "Disneyland Paris",
            "lat": 48.8674,
            "lng": 2.7836
        }
    }

    def get_park_info(self, name_or_id: str) -> Optional[Dict[str, Any]]:
        """Retorna dados estáticos do parque (lat, lng, id)"""
        if name_or_id in self.PARK_DATA:
            return self.PARK_DATA[name_or_id]
            
        for key, data in self.PARK_DATA.items():
            if data["name"].lower() == name_or_id.lower() or data["id"] == name_or_id:
                return data
        return None

    def get_live_data(self, park_name_or_id: str) -> List[Dict[str, Any]]:
        """Busca tempos de espera e status das atrações"""
        park_info = self.get_park_info(park_name_or_id)
        park_id = park_info["id"] if park_info else park_name_or_id
        
        url = f"{self.BASE_URL}/entity/{park_id}/live"
        logger.info(f"🎢 Buscando dados em tempo real para o parque: {park_id}")
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get("liveData", [])
        except Exception as e:
            logger.error(f"Erro ao buscar dados do parque {park_id}: {e}")
            return []

    def format_park_summary(self, live_data: List[Dict[str, Any]], limit: int = 15) -> str:
        """Formata um resumo legível dos tempos de espera"""
        if not live_data:
            return "Nenhum dado em tempo real disponível para este parque no momento."
            
        # Filtrar apenas atrações com tempo de espera (ou status relevante)
        attractions = []
        for item in live_data:
            if item.get("entityType") == "ATTRACTION":
                name = item.get("name")
                status = item.get("status", "OPERATING")
                wait_time = item.get("queue", {}).get("STANDBY", {}).get("waitTime")
                
                if status != "OPERATING":
                    attractions.append(f"❌ *{name}*: {status}")
                elif wait_time is not None:
                    attractions.append(f"⏱️ *{name}*: {wait_time} min")
                else:
                    attractions.append(f"✅ *{name}*: Aberto")

        # Ordenar por tempo de espera (opcional) e limitar
        summary = "\n".join(attractions[:limit])
        return (
            "🎢 **STATUS DO PARQUE EM TEMPO REAL** 🎡\n\n"
            f"{summary}\n\n"
            "💡 *Dica do Seven:* Recomendo ir nos brinquedos com menos de 20 min agora!"
        )

    def find_park_id_by_name(self, name: str) -> Optional[str]:
        """Tenta encontrar o ID do parque via busca na API (opcional)"""
        # Para o MVP, usaremos os IDs fixos ou o usuário passa o ID.
        return self.PARK_IDS.get(name.lower().replace(" ", "_"))
