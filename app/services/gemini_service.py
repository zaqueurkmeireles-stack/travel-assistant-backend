"""
Gemini Service - Inteligência Alternativa para Debate e Robustez
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from app.config import settings
from loguru import logger
from typing import List, Dict, Optional

class GeminiService:
    """Service para integração com Google Gemini (Segunda Opinião)"""
    
    def __init__(self):
        """Inicializa o cliente Gemini usando LangChain"""
        if settings.GOOGLE_GEMINI_API_KEY:
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash", 
                google_api_key=settings.GOOGLE_GEMINI_API_KEY,
                temperature=0.7,
                max_retries=0 # 🛡️ Falha rápido para não travar o usuário
            )
            logger.info("✅ Gemini Service inicializado (Retries desativados)")
        else:
            self.llm = None
            logger.warning("⚠️ Chave do Gemini não configurada.")
            
    def get_second_opinion(self, original_plan: str, real_tips: str) -> Optional[str]:
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
            if "429" in str(e) or "quota" in str(e).lower():
                logger.error(f"🛑 COTÁ EXCEDIDA NO GEMINI (429): {e}")
            else:
                logger.error(f"Erro ao consultar Gemini: {e}")
            return None

    def verify_navigation_and_arrival(self, assistant_response: str, user_query: str) -> Optional[str]:
        """
        Revisão especializada para navegação e chegada em aeroportos/destinos.
        Evita alucinações em números de esteiras, plataformas e direções.
        """
        if not self.llm:
            return None
            
        prompt = (
            "Você é um Auditor de Segurança em Viagens. Sua tarefa é revisar a resposta de outro assistente de IA.\n"
            "Foco: Navegação em Aeroportos, Esteiras de Bagagem e Transporte Público.\n\n"
            f"Pergunta do Usuário: {user_query}\n"
            f"Resposta da Outra IA: {assistant_response}\n\n"
            "REGRAS DE AUDITORIA:\n"
            "1. Verifique se os números de esteira ou plataformas citados fazem sentido ou se parecem alucinação.\n"
            "2. Se a IA disse 'Vá para a esteira X', verifique se ela realmente encontrou isso nos documentos. "
            "Se for uma suposição, você deve corrigir para: 'Verifique no painel do aeroporto'.\n"
            "3. Verifique se o link do Google Maps é coerente com o destino.\n"
            "4. Se houver erro, corrija educadamente. Se estiver perfeito, apenas valide.\n\n"
            "Responda apenas com a melhor versão refinada da instrução de navegação."
        )
        
        try:
            response = self.llm.invoke(prompt)
            return response.content
        except Exception as e:
            if "429" in str(e) or "quota" in str(e).lower():
                logger.error(f"🛑 COTÁ EXCEDIDA NO GEMINI NAVEGAÇÃO (429): {e}")
            else:
                logger.error(f"Erro ao auditar navegação com Gemini: {e}")
            return None
