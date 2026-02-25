"""
Connectivity Service - Recomendações de Chip e eSIM para o exterior
"""

from app.services.search_service import SearchService
from loguru import logger

class ConnectivityService:
    """Service para recomendar opções de internet no exterior"""
    
    def __init__(self):
        self.search_svc = SearchService()
        logger.info("✅ Connectivity Service inicializado")
        
    def get_e_sim_recommendations(self, destination: str) -> str:
        """
        Busca as melhores opções de chip/eSIM para o destino específico.
        """
        logger.info(f"📶 Buscando opções de internet para {destination}")
        
        # Usamos o SearchService para ter dados sempre atualizados
        topic = "melhores chips de viagem eSIM airalo holafly operadoras locais dicas"
        search_result = self.search_svc.search_real_experiences(destination, topic)
        
        prompt_intro = (
            f"📶 **Conectividade em {destination}:**\n"
            "Existem 3 formas principais de ter internet:\n\n"
            "1. **eSIM Internacional (Recomendado)**: Opções como **Airalo** ou **Holafly** (instala antes de sair do Brasil).\n"
            "2. **Chip Local**: Mais barato, mas precisa comprar ao chegar.\n"
            "3. **Roaming Operadora**: Geralmente o mais caro (use apenas em emergência).\n\n"
            "**Dicas baseadas em pesquisas atuais:**\n"
        )
        
        return f"{prompt_intro}{search_result}"
