"""
Claude Service - Inteligência Alternativa (Anthropic) para Refinamento e Consenso
"""

from langchain_anthropic import ChatAnthropic
from app.config import settings
from loguru import logger
from typing import Optional

class ClaudeService:
    """Service para integração com Anthropic Claude (Consenso de Especialistas)"""
    
    def __init__(self):
        """Inicializa o cliente Claude usando LangChain"""
        if settings.ANTHROPIC_API_KEY:
            self.llm = ChatAnthropic(
                model="claude-3-5-sonnet-20240620",
                api_key=settings.ANTHROPIC_API_KEY,
                temperature=0.7,
                max_retries=0 # 🛡️ Falha rápido para não travar o usuário
            )
            logger.info("✅ Claude Service inicializado (Retries desativados)")
        else:
            self.llm = None
            logger.warning("⚠️ Chave do Claude não configurada.")
            
    def get_refined_answer(self, user_query: str, original_plan: str, gemini_opinion: str = "") -> Optional[str]:
        """
        Recebe o roteiro original e a opinião do Gemini (se houver) 
        para gerar um veredito final ou refinamento de alto nível.
        """
        if not self.llm:
            return "Claude não configurado para debate."
            
        consensus_context = ""
        if gemini_opinion:
            consensus_context = f"\nO Gemini sugeriu as seguintes melhorias:\n{gemini_opinion}"

        prompt = (
            "Você é um consultor VIP de viagens especializado em detalhes luxuosos e práticos.\n"
            f"Pergunta do Usuário: {user_query}\n\n"
            f"Resposta Proposta (GPT-4):\n{original_plan}\n"
            f"{consensus_context}\n\n"
            "Sua tarefa é revisar essas informações e entregar a RESPOSTA FINAL ao usuário.\n"
            "Seja elegante, direto e corrija qualquer imprecisão baseada no seu conhecimento vasto.\n"
            "Entregue apenas o texto final polido."
        )
        
        try:
            response = self.llm.invoke(prompt)
            return response.content
        except Exception as e:
            if "429" in str(e) or "quota" in str(e).lower() or "credit balance" in str(e).lower():
                logger.warning("🛡️ Claude: Sem saldo ou cota atingida. Seguindo sem refinamento.")
            else:
                logger.error(f"❌ Erro Claude: {e}")
            return None
