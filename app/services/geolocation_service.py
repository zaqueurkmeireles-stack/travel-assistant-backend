"""
Geolocation Service - Gerencia localização do usuário e fornece guia de chegada.
"""

from loguru import logger
from typing import Dict, Any, Optional
from app.services.maps_service import GoogleMapsService
from app.services.trip_service import TripService

class GeolocationService:
    """Gerencia a localização do usuário e provê assistência baseada em geofencing simples"""
    
    def __init__(self):
        self.maps_svc = GoogleMapsService()
        self.trip_svc = TripService()
        logger.info("✅ GeolocationService inicializado")
        
    def process_location(self, user_id: str, lat: float, lng: float) -> Optional[str]:
        """
        Processa coordenadas e verifica se o usuário chegou ao destino de uma viagem ativa.
        Retorna uma mensagem de boas-vindas/guia se detectado.
        """
        logger.info(f"📍 Localização recebida de {user_id}: ({lat}, {lng})")
        
        # 1. Buscar viagens ativas hoje para este usuário
        from datetime import datetime
        today = datetime.now().date()
        
        active_trip = None
        for trip in self.trip_svc.trips:
            if trip["user_id"] == user_id:
                start_dt = datetime.strptime(trip["start_date"], "%Y-%m-%d").date()
                if start_dt <= today and not trip.get("arrival_guide_sent", False):
                    active_trip = trip
                    break
        
        if not active_trip:
            return None
            
        # 2. Verificar proximidade com o destino (Geocoding do destino)
        dest_name = active_trip["destination"]
        dest_loc = self.maps_svc.geocode(dest_name)
        
        if not dest_loc:
            return None
            
        # Distância aproximada simples (haversine ou similar - aqui simplificado para MVP)
        distance = self._calculate_distance(lat, lng, dest_loc["lat"], dest_loc["lng"])
        
        # Se estiver a menos de 50km do centro da cidade/aeroporto
        if distance < 50:
            logger.info(f"🛬 Usuário {user_id} detectado em {dest_name}!")
            active_trip["arrival_guide_sent"] = True
            self.trip_svc._save_trips()
            return self._generate_arrival_guide(dest_name, user_id)
            
        return None

    def _calculate_distance(self, lat1, lon1, lat2, lon2):
        """Calcula distância aproximada em KM (Simplificado)"""
        import math
        R = 6371 # Raio da Terra
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c

    def _generate_arrival_guide(self, destination: str, user_id: str) -> str:
        """Gera guia de 'Boas-vindas' com informações úteis de baixo consumo de dados"""
        # Aqui poderíamos chamar o Agente ou usar um template rico
        return (
            f"📍 *Bem-vindo a {destination}!* 🛬\n\n"
            "Detectei que você acabou de chegar. Aqui estão algumas dicas rápidas para facilitar seu desembarque:\n\n"
            "🎫 *Transporte:* O aeroporto possui conexão direta via trem (S-Bahn) e táxis oficiais no Terminal 1.\n"
            "📶 *Dica de Dados:* Evite baixar mapas grandes agora. Se precisar de direções, me peça 'instruções em texto' para economizar bateria e roaming.\n"
            "🏨 *Seu Hotel:* Lembre-se que você tem uma reserva no *Steigenberger Icon*. Quer que eu te dê o endereço exato?"
        )
