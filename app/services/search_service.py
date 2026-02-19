"""
Search Service - Busca de dicas reais na internet via Tavily
"""

import requests
from app.config import settings
from loguru import logger
from typing import Optional, Dict

class SearchService:
    """Service para buscar informações em tempo real e relatos em fóruns"""
    
    def __init__(self):
        self.api_key = settings.TAVILY_API_KEY
        self.base_url = "https://api.tavily.com/search"
        if self.api_key:
            logger.info("✅ Search Service (Tavily) inicializado")
        else:
            logger.warning("⚠️ Tavily API Key não configurada.")
            
    def search_real_experiences(self, destination: str, topic: str = "dicas e perrengues") -> str:
        """
        Busca relatos profundos focando em fóruns e blogs reais.
        """
        if not self.api_key:
            return "Busca na internet indisponível (Chave não configurada)."
            
        query = f"relatos de viagem {destination} reddit forums blogs {topic}"
        
        payload = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": "advanced",
            "include_answer": True,
            "max_results": 5
        }
        
        try:
            response = requests.post(self.base_url, json=payload, timeout=15)
            data = response.json()
            
            if response.status_code == 200:
                answer = data.get("answer", "")
                results = "\n".join([f"- {res['title']}: {res['content'][:200]}..." for res in data.get("results", [])])
                return f"Resumo da Comunidade:\n{answer}\n\nFontes Diretas:\n{results}"
            else:
                logger.error(f"Erro Tavily: {data}")
                return "Erro ao processar buscas na internet."
                
        except Exception as e:
            logger.error(f"Erro no SearchService: {e}")
            return "Falha de conexão ao buscar experiências."
