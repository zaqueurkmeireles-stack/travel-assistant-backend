"""
Geolocation Service - Gerencia localização do usuário e fornece guia de chegada.
"""

from loguru import logger
from app.services.maps_service import GoogleMapsService
from app.services.trip_service import TripService
from app.services.park_service import ParkService
from typing import Optional, Dict, Any, List

class GeolocationService:
    """Gerencia a localização do usuário e provê assistência baseada em geofencing simples"""
    
    def __init__(self):
        self.maps_svc = GoogleMapsService()
        self.trip_svc = TripService()
        self.park_svc = ParkService()
        self.PROXIMITY_RADIUS_KM = 2.0  # Raio para dicas de destino
        self.PARK_RADIUS_KM = 0.5       # Raio para ativar Modo Parque
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
                # REGRA: Somente monitorar/ser proativo se a viagem já começou
                if start_dt <= today:
                    active_trip = trip
                    # Se for exatamente o dia do início e ainda não enviamos o guia, marcar para enviar
                    if start_dt == today and not trip.get("arrival_guide_sent", False):
                        # Nota: A lógica de envio real fica no orchestrator/webhook
                        pass
                    break
        
        if not active_trip:
            logger.debug(f"ℹ️ Nenhuma viagem ativa ou iniciada para {user_id} hoje. Ignorando geolocalização proativa.")
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
            
        # 4. Verificar proximidade com parques temáticos (Disney, Universal, Europa Park, etc.)
        for park_key, park_info in self.park_svc.PARK_DATA.items():
            park_lat = park_info["lat"]
            park_lng = park_info["lng"]
            park_distance = self._calculate_distance(lat, lng, park_lat, park_lng)
            
            if park_distance <= self.PARK_RADIUS_KM:
                logger.info(f"🎉 Usuário {user_id} próximo de {park_info['name']} (distância: {park_distance:.2f}km)")
                
                # Marcar que o usuário está "No Parque" para o monitoramento proativo
                active_trip["current_park_id"] = park_info["id"]
                active_trip["current_park_name"] = park_info["name"]
                
                # Cooldown para não spammar o guia do parque
                last_park_guide_time = active_trip.get("last_park_guide_sent_at", {}).get(park_info['id'])
                should_send_park_guide = True
                if last_park_guide_time:
                    try:
                        last_dt = datetime.fromisoformat(last_park_guide_time)
                        if (datetime.now() - last_dt).total_seconds() < 3600: # 1 hora de cooldown
                            should_send_park_guide = False
                    except:
                        pass
                
                if should_send_park_guide:
                    guide_message = self._trigger_park_mode_guide(park_info['id'], user_id)
                    if "last_park_guide_sent_at" not in active_trip:
                        active_trip["last_park_guide_sent_at"] = {}
                    active_trip["last_park_guide_sent_at"][park_info['id']] = datetime.now().isoformat()
                    self.trip_svc._save_trips()
                    return guide_message
            
        # Se saiu do parque, remover a flag
        if "current_park_id" in active_trip:
            # Só remove se estiver realmente longe (histerese de 1km)
            park_info = self.park_svc.get_park_info(active_trip["current_park_id"])
            if park_info:
                dist = self._calculate_distance(lat, lng, park_info["lat"], park_info["lng"])
                if dist > 1.0:
                    logger.info(f"👋 Usuário saiu do parque {park_info['name']}")
                    del active_trip["current_park_id"]
                    del active_trip["current_park_name"]
                    self.trip_svc._save_trips()
            
        return None

    def _trigger_park_mode_guide(self, park_id: str, user_id: str) -> str:
        """Gera um guia proativo em tempo real para o parque"""
        logger.info(f"🎢 Gerando Guia de Parque para {park_id}...")
        
        from app.agents.orchestrator import TravelAgent
        agent = TravelAgent()
        
        prompt = (
            f"O usuário acaba de entrar no parque temático: **{park_id}**. "
            "Sua missão é dar as boas-vindas ao parque e fornecer um resumo em tempo real dos tempos de espera. "
            "1. Chame a ferramenta 'get_park_live_status' para o parque atual.\n"
            "2. Analise os tempos e sugira uma rota inteligente (quais brinquedos ir agora e quais evitar).\n"
            "3. Deseje um dia mágico e lembre que você pode guiá-lo pelo mapa se ele se perder."
        )
        
        msg = agent.chat(user_input=prompt, thread_id=user_id)
        return msg

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
