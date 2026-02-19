"""
Gemini Service - Inteligência Alternativa para Debate e Robustez
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from app.config import settings
from loguru import logger
from typing import List, Dict

class GeminiService:
    """Service para integração com Google Gemini (Segunda Opinião)"""
    
    def __init__(self):
        """Inicializa o cliente Gemini usando LangChain"""
        if settings.GOOGLE_GEMINI_API_KEY:
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash", 
                google_api_key=settings.GOOGLE_GEMINI_API_KEY,
                temperature=0.7
            )
            logger.info("✅ Gemini Service inicializado")
        else:
            self.llm = None
            logger.warning("⚠️ Chave do Gemini não configurada.")
            
    def get_second_opinion(self, original_plan: str, real_tips: str) -> str:
        """
        Analisa o roteiro principal e as dicas reais da internet 
        para sugerir melhorias práticas ou identificar problemas.
        """
        if not self.llm:
            return "Gemini não configurado para debate."
            
        prompt = (
            "Você é um consultor de viagens experiente e pragmático.\n"
            f"Plano Original:\n{original_plan}\n\n"
            f"Relatos reais de quem já foi (Internet):\n{real_tips}\n\n"
            "Com base nos relatos reais, aponte potenciais pegadinhas, ajuste o roteiro "
            "e traga uma resposta robusta melhorando a ideia original."
        )
        
        try:
            response = self.llm.invoke(prompt)
            return response.content
        except Exception as e:
            logger.error(f"Erro ao consultar Gemini: {e}")
            return f"Erro na análise secundária: {str(e)}"
