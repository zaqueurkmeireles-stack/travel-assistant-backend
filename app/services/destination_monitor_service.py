"""
Destination Monitor Service - Pesquisa proativa de fechamentos ou manutenção em atrações.
"""

from loguru import logger
from typing import List, Dict, Any, Optional
from app.services.openai_service import OpenAIService
from app.services.n8n_service import N8nService

class DestinationMonitorService:
    """Service para monitorar status de POIs (Pontos de Interesse) via Web Search"""
    
    def __init__(self):
        self.openai_svc = OpenAIService()
        self.n8n_svc = N8nService()
        logger.info("✅ DestinationMonitorService inicializado")

    def check_poi_status(self, poi_name: str, date_hint: str) -> Optional[str]:
        """
        Gera um relatório sobre o status de uma atração.
        Nota: O Agente executará a busca real, este service formata o alerta se houver problema.
        """
        logger.info(f"🔍 Auditando status de: {poi_name} para a data {date_hint}")
        # A lógica real de busca será orquestrada pelo agente no scheduler
        return None

    def format_closure_alert(self, poi_name: str, issue_details: str, date: str) -> str:
        """Formata a mensagem de alerta de fechamento/manutenção"""
        return (
            f"📢 **ALERTA DE DESTINO: {poi_name.upper()}** ⚠️\n\n"
            f"Olá! Fiz uma varredura proativa e notei um detalhe importante para o dia {date}:\n"
            f"❌ **O que encontrei**: {issue_details}\n\n"
            f"Parece que o local estará em manutenção ou fechado. Deseja que eu procure uma alternativa semelhante ou ajuste seu roteiro?"
        )
