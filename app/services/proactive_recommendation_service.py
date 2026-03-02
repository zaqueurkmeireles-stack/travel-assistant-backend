"""
Proactive Recommendation Service - Motor de descobertas locais e cupons.
"""

from loguru import logger
from typing import List, Dict, Any, Optional
from app.services.maps_service import GoogleMapsService
from app.services.openai_service import OpenAIService
from app.services.search_service import SearchService
from app.services.trip_service import TripService
import json

class ProactiveRecommendationService:
    """Service para encontrar joias locais (gems) e gerar dicas proativas."""
    
    def __init__(self):
        self.maps_svc = GoogleMapsService()
        self.openai_svc = OpenAIService()
        self.search_svc = SearchService()
        self.trip_svc = TripService()
        logger.info("✅ ProactiveRecommendationService inicializado")

    def get_nearby_gems(self, lat: float, lng: float, user_id: str) -> List[Dict]:
        """Busca lugares de alta qualidade (restaurantes 4.5+ e atrações 4.0+) próximos ao usuário."""
        # 1. Buscar atrações turísticas
        attractions = self.maps_svc.find_nearby_places(lat, lng, place_type="tourist_attraction", radius=2000)
        gems = [g for g in attractions if g.get("rating", 0) >= 4.0]

        # 2. Buscar restaurantes e cafés de elite (4.5+)
        food_places = self.maps_svc.find_nearby_places(lat, lng, place_type="restaurant", radius=1000)
        food_places += self.maps_svc.find_nearby_places(lat, lng, place_type="cafe", radius=1000)
        
        # Filtrar por rating alto e evitar duplicatas
        seen_names = set(g["name"] for g in gems)
        for f in food_places:
            if f["name"] not in seen_names and f.get("rating", 0) >= 4.5:
                # Adicionar tag de "Elite" para o prompt da IA
                f["is_elite_food"] = True
                gems.append(f)
                seen_names.add(f["name"])

        return gems

    def generate_proactive_tip(self, user_id: str, lat: float, lng: float) -> Optional[str]:
        """Gera uma dica personalizada e proativa baseada na localização atual e contexto."""
        # 1. Identificar onde o usuário está exatamente
        address = self.maps_svc.reverse_geocode(lat, lng)
        logger.info(f"📍 Gerando dica proativa para {user_id} em {address}")

        # 2. Buscar gems e contexto da viagem (ex: crianças)
        gems = self.get_nearby_gems(lat, lng, user_id)
        
        # 3. Verificar se há crianças na viagem (usando RAG ou metadados da trip)
        has_kids = False
        trip_id = self.trip_svc.get_active_trip(user_id)
        if trip_id:
            # Tentar inferir do resumo da viagem ou metadados
            # Para o MVP, assumimos False a menos que o RAG diga o contrário em uma busca rápida
            from app.services.rag_service import RAGService
            rag = RAGService()
            rag_context = rag.query("viajantes e crianças", user_id, k=2)
            if "criança" in rag_context.lower() or "filho" in rag_context.lower():
                has_kids = True

        if not gems:
            return None

        # 4. Usar OpenAI para criar a mensagem "Concierge"
        prompt = (
            f"O usuário está em {address} ({lat}, {lng}). "
            f"Sugestões de ELITE detectadas (Rating 4.5+ ou Gems): {json.dumps(gems[:3])}.\n"
            f"Contexto: {'Viajando com crianças' if has_kids else 'Viajante solo/casal'}.\n"
            "Sua missão: Escreva uma dica de concierge PROATIVA, CURTA e ENCANTADORA.\n"
            "- Foque na 'Excelente Reputação' dos lugares e no 'Melhor Custo-Benefício' da região.\n"
            "- Se houver lugares com 'is_elite_food', destaque como uma experiência gastronômica imperdível.\n"
            "- Se estiver em uma cidade pequena ou interior (ex: Baviera), use um tom de 'descoberta de jóia escondida'.\n"
            "- Seja muito cordial e proativo. Ex: 'Vi que você está perto de um dos melhores restaurantes da região...'"
        )

        try:
            tip = self.openai_svc.analyze_text(prompt)
            return tip
        except Exception as e:
            logger.error(f"Erro ao gerar dica proativa: {e}")
            return None

    def search_discounts_proactively(self, place_name: str, city: str) -> Optional[str]:
        """Busca cupons ou descontos reais para um local específico via Tavily/Search."""
        logger.info(f"🎟️ Buscando descontos para {place_name} em {city}")
        query = f"cupom de desconto ingresso outlet ofertas {place_name} {city}"
        return self.search_svc.search_real_experiences(city, query)
