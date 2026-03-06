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
        # Removed: self.trip_svc = TripService()
        logger.info("✅ ProactiveRecommendationService inicializado")

    def _safe_rating(self, rating: Any) -> float:
        """Converte a avaliação para float, tratando possíveis erros e retornando 0.0 se inválido."""
        try:
            return float(rating)
        except (ValueError, TypeError):
            return 0.0

    def get_nearby_gems(self, lat: float, lng: float, user_id: str) -> List[Dict]:
        """Busca lugares de alta qualidade (restaurantes 4.5+, atrações 4.0+ e Shoppings) próximos ao usuário."""
        # 1. Buscar atrações turísticas
        attractions = self.maps_svc.find_nearby_places(lat, lng, place_type="tourist_attraction", radius=2000)
        gems = [g for g in attractions if self._safe_rating(g.get("rating")) >= 4.0]

        # 2. Buscar restaurantes e cafés de elite (4.5+)
        food_places = self.maps_svc.find_nearby_places(lat, lng, place_type="restaurant", radius=1000)
        food_places += self.maps_svc.find_nearby_places(lat, lng, place_type="cafe", radius=1000)
        
        # 3. Buscar Compras de Alto Valor (Outlets, Malls, Department Stores)
        shopping = self.maps_svc.find_nearby_places(lat, lng, place_type="shopping_mall", radius=3000)
        shopping += self.maps_svc.find_nearby_places(lat, lng, place_type="department_store", radius=2000)
        
        # Filtrar por rating alto e evitar duplicatas
        seen_names = set(g["name"] for g in gems)
        
        # Add Food
        for f in food_places:
            if f["name"] not in seen_names and self._safe_rating(f.get("rating")) >= 4.5:
                f["is_elite_food"] = True
                gems.append(f)
                seen_names.add(f["name"])
        
        # Add Shopping
        for s in shopping:
            rating = self._safe_rating(s.get("rating"))
            if s["name"] not in seen_names and (rating >= 4.0 or "outlet" in s["name"].lower()):
                s["is_shopping"] = True
                gems.append(s)
                seen_names.add(s["name"])

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
        from app.services.user_service import UserService # Import moved inside function
        user_svc = UserService() # Instantiate UserService
        trip_id = user_svc.get_active_trip(user_id) # Use UserService to get active trip
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

        # 4. Filtrar duplicatas contra o RAG (não sugerir o que já está no roteiro)
        from app.services.rag_service import RAGService
        rag = RAGService()
        filtered_gems = []
        
        for gem in gems[:5]: # Verificar os top 5
            # Busca rápida no RAG pelo nome do lugar
            query = f"O lugar '{gem['name']}' já está planejado ou no roteiro da viagem?"
            rag_result = rag.query(query, user_id, k=2)
            
            # Se o RAG indicar que já está planejado, ignorar
            if any(word in rag_result.lower() for word in ["sim", "planejado", "agendado", "no roteiro", "reserva"]):
                logger.info(f"⏭️ Pulando '{gem['name']}' pois já consta no roteiro (RAG Match).")
                continue
            filtered_gems.append(gem)

        if not filtered_gems:
            logger.info("ℹ️ Todas as sugestões próximas já estão no roteiro. Nada a sugerir no momento.")
            return None

        # 5. Usar OpenAI para criar a mensagem "Concierge"
        prompt = (
            f"O usuário está em {address} ({lat}, {lng}). "
            f"Sugestões INÉDITAS (NÃO estão no roteiro) detectadas: {json.dumps(filtered_gems[:3])}.\n"
            f"Contexto: {'Viajando com crianças' if has_kids else 'Viajante solo/casal'}.\n"
            "Sua missão: Escreva uma dica de concierge PROATIVA, CURTA e ENCANTADORA.\n"
            "- Foque na 'Excelente Reputação' dos lugares e no 'Melhor Custo-Benefício' (Especialmente para Compras/Shopping).\n"
            "- Se houver 'is_shopping', destaque ofertas ou o valor da experiência de compra.\n"
            "- Se houver 'is_elite_food', destaque como uma experiência gastronômica imperdível.\n"
            "- Mencione sutilmente que esta é uma nova descoberta que não estava planejada originalmente.\n"
            "- Se estiver em uma cidade pequena ou interior (ex: Baviera), use um tom de 'joia escondida'.\n"
            "- Seja muito cordial e proativo."
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
