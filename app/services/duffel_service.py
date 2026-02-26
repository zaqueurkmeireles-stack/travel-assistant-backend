"""
Duffel Service - Busca de voos reais com inventário direto
"""

from duffel_api import Duffel
from app.config import settings
from loguru import logger
from typing import List, Dict, Optional
from datetime import datetime

class DuffelService:
    """Service para integração com Duffel (Busca de Voos)"""
    
    def __init__(self):
        """Inicializa o cliente Duffel"""
        if settings.DUFFEL_API_KEY:
            # O SDK gerencia a versão internamente, remover o parâmetro explícito que causou erro no adapter
            self.client = Duffel(access_token=settings.DUFFEL_API_KEY)
            logger.info("✅ Duffel Service inicializado")
        else:
            self.client = None
            logger.warning("⚠️ Chave do Duffel não configurada.")
            
    def search_flights(self, origin: str, destination: str, departure_date: str, return_date: Optional[str] = None) -> str:
        """
        Busca ofertas de voos reais.
        origin/destination: Códigos IATA (ex: GRU, CDG)
        departure_date: YYYY-MM-DD
        """
        if not self.client:
            return "Duffel não configurado para busca de voos."
            
        try:
            logger.info(f"✈️ Buscando voos: {origin} -> {destination} em {departure_date}")
            
            slices = [
                {
                    "origin": origin,
                    "destination": destination,
                    "departure_date": departure_date,
                }
            ]
            
            if return_date:
                slices.append({
                    "origin": destination,
                    "destination": origin,
                    "departure_date": return_date,
                })
                
            offer_request = self.client.offer_requests.create() \
                .passengers([{"type": "adult"}]) \
                .slices(slices) \
                .return_offers() \
                .execute()
            
            offers = offer_request.offers
            
            if not offers:
                return f"Nenhum voo encontrado entre {origin} e {destination} para as datas informadas."
                
            # Formatar as top 3 ofertas
            result = f"✈️ **Encontrei as melhores ofertas de voos para você:**\n\n"
            
            for i, offer in enumerate(offers[:3], 1):
                total_amount = offer.total_amount
                total_currency = offer.total_currency
                airline = offer.owner.name
                
                # Pegar detalhes do primeiro segmento da ida
                first_slice = offer.slices[0]
                departure_time = first_slice.segments[0].departing_at
                arrival_time = first_slice.segments[-1].arriving_at
                
                result += f"{i}. **{airline}**\n"
                result += f"   💰 Preço Total: {total_amount} {total_currency}\n"
                result += f"   🛫 Partida: {departure_time}\n"
                result += f"   🛬 Chegada: {arrival_time}\n"
                if len(offer.slices) > 1:
                    result += f"   🔄 (Voo de Ida e Volta incluso)\n"
                result += "\n"
                
            result += "Para reservar ou ver mais detalhes, me avise!"
            return result
            
        except Exception as e:
            logger.error(f"Erro ao buscar voos no Duffel: {e}")
            return f"Erro ao consultar disponibilidade de voos: {str(e)}"
