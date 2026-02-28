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
        
        # 3. Auditoria de Proximidade (Gaps e Recomendações)
        # Cooldown para não spammar (ex: apenas 1 dica proativa a cada 6 horas)
        last_tip_time = active_trip.get("last_proactive_tip_at")
        should_send_tip = True
        if last_tip_time:
            try:
                last_dt = datetime.fromisoformat(last_tip_time)
                if (datetime.now() - last_dt).total_seconds() < 21600: # 6 horas
                    should_send_tip = False
            except:
                pass

        if should_send_tip:
            from app.services.proactive_recommendation_service import ProactiveRecommendationService
            rec_svc = ProactiveRecommendationService()
            tip = rec_svc.generate_proactive_tip(user_id, lat, lng)
            
            if tip:
                active_trip["last_proactive_tip_at"] = datetime.now().isoformat()
                self.trip_svc._save_trips()
                return tip
            
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

    def _generate_intelligent_arrival_guide(self, destination: str, user_id: str) -> str:
        """Gera guia de 'Boas-vindas' proativo usando IA e documentos do RAG"""
        from app.agents.orchestrator import TravelAgent
        agent = TravelAgent()
        
        prompt = (
            f"O usuário acabou de chegar em {destination}. "
            f"Analise os documentos dele no RAG (voos, hotéis, aluguel de carro) e gere um guia de chegada CURTO e EXTREMAMENTE ÚTIL.\n\n"
            "Inclua se encontrar:\n"
            "- Nome da locadora de veículos e onde fica o guichê (se houver aluguel).\n"
            "- Endereço do hotel e se o check-in já está disponível.\n"
            "- Como sair do aeroporto (Dica rápida de transporte).\n"
            "- Pergunte se ele quer que você salve um MAPA OFFLINE para economizar dados ou se prefere direções por texto.\n\n"
            "Seja carinhoso e proativo, como um guia especializado local."
        )
        
        try:
            # Chamada direta ao agente para gerar o guia proativo
            guide = agent.chat(user_input=f"[SISTEMA: GUIA DE CHEGADA EM {destination}] {prompt}", thread_id=user_id)
            return guide
        except Exception as e:
            logger.error(f"Erro ao gerar guia inteligente: {e}")
            return f"📍 *Bem-vindo a {destination}!* 🛬\n\nQue bom que você chegou! Como posso te ajudar com os primeiros passos da sua viagem?"
