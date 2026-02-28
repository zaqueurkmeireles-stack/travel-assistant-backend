"""
Event Service - Pesquisa inteligente de detalhes de eventos (F1, Shows, Festivais).
"""

from loguru import logger
from typing import Dict, Any, Optional, List
from app.services.openai_service import OpenAIService

class EventService:
    """Service para pesquisar e estruturar informações sobre locais de eventos específicos"""
    
    def __init__(self):
        self.openai_svc = OpenAIService()
        logger.info("✅ EventService inicializado")

    def research_venue_details(self, event_name: str, venue_name: str) -> str:
        """
        Usa busca web (via ferramenta do agente) para extrair detalhes do layout do evento.
        Nota: Esta lógica será guiada pelo Agente usando as ferramentas de busca,
        mas o service pode formatar ou sugerir o que buscar.
        """
        logger.info(f"🏎️ Solicitando pesquisa de layout para {event_name} em {venue_name}")
        
        # Esta função serve mais como um template de prompts para o Agente
        # do que uma chamada de API direta, já que layouts de eventos variam muito.
        return f"Preciso que você pesquise os detalhes de acesso para o evento '{event_name}' no local '{venue_name}'."

    def format_event_advisory(self, event_context: Dict[str, Any]) -> str:
        """Formata uma mensagem proativa de conselhos para o evento (Clima, Itens, Portões)"""
        event_name = event_context.get("name", "Evento")
        venue = event_context.get("venue", "Local")
        gate = event_context.get("gate", "Verifique seu ingresso")
        weather = event_context.get("weather_hint", "Verifique a previsão")
        
        advice = (
            f"🏎️ **PREPARAÇÃO PARA {event_name.upper()}** 🏁\n\n"
            f"📍 **Local**: {venue}\n"
            f"🚪 **Seu Portão**: {gate}\n\n"
            "💡 **Dicas do Seven Concierge:**\n"
        )
        
        if "chuva" in weather.lower() or "rain" in weather.lower():
            advice += "- ☔ **ALERTA**: Há previsão de chuva! Recomendo comprar uma capa de chuva antes de ir ao local, pois lá costumam ser muito caras.\n"
        
        advice += "- 🧴 Não esqueça o protetor solar e hidratação.\n"
        advice += "- 🎫 Tenha seu ingresso digital offline ou printado.\n"
        advice += "- 🗺️ Se precisar de ajuda para chegar ao banheiro ou praça de alimentação mais próxima, é só me pedir o mapa!"
        
        return advice
