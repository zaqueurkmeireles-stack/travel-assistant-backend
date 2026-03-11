import asyncio
from loguru import logger
from typing import List, Dict, Optional

from app.services.openai_service import OpenAIService
from app.services.gemini_service import GeminiService

class AIOrchestrator:
    def __init__(self):
        self.openai = OpenAIService()
        self.gemini = GeminiService()
        self.priority_order = ["GPT-4o-Mini", "Claude", "Gemini"]

    async def _fetch_response(self, ai_name: str, ai_method, prompt: str) -> Optional[Dict[str, str]]:
        if ai_method is None:
            logger.warning(f"[{ai_name}] Método de chamada não configurado (None).")
            return None
            
        try:
            logger.info(f"[{ai_name}] Iniciando processamento...")
            response = await asyncio.to_thread(ai_method, prompt) 
            
            content = ""
            if hasattr(response, 'content'):
                content = response.content
            elif hasattr(response, 'choices'):
                content = response.choices[0].message.content
            elif isinstance(response, str):
                content = response
            elif isinstance(response, dict) and "text" in response:
                content = response["text"]
            
            if content:
                logger.success(f"[{ai_name}] Respondeu com sucesso.")
                return {"name": ai_name, "content": content}
            return None
        except Exception as e:
            logger.warning(f"[{ai_name}] Falhou ou sem saldo: {str(e)}")
            return None

    async def process_message(self, prompt: str) -> str:
        logger.info("🧠 Iniciando Conselho de IAs (GPT > Claude > Gemini)...")
        
        # Aqui está o pulo do gato: chamando a função exata que achamos no Raio-X
        tasks = [
            self._fetch_response("GPT-4o-Mini", self.openai.analyze_text, prompt),
            self._fetch_response("Gemini", getattr(self.gemini.llm, 'invoke', None) if hasattr(self.gemini, 'llm') else None, prompt)
        ]
        
        tasks = [t for t in tasks if t is not None]
        results = await asyncio.gather(*tasks)
        
        survivors = [res for res in results if res is not None]
        survivors_count = len(survivors)
        
        if survivors_count == 0:
            logger.critical("⚠️ Todas as IAs falharam (Zero tokens no sistema ou erro de rede).")
            raise Exception("Nenhuma IA disponível no momento.")
            
        elif survivors_count == 1:
            winner = survivors[0]["name"]
            logger.info(f"🥇 Apenas {winner} respondeu. Repassando resposta direta sem consenso.")
            return survivors[0]["content"]
            
        else:
            names = [r["name"] for r in survivors]
            logger.info(f"🤝 Consenso ativado entre {survivors_count} IAs: {', '.join(names)}")
            
            combined_texts = "\n\n".join([f"--- Visão do {r['name']} ---\n{r['content']}" for r in survivors])
            consensus_prompt = (
                "Você é o Concierge Master de Viagens. Abaixo estão análises de diferentes assistentes.\n"
                f"{combined_texts}\n\n"
                "Sua tarefa: Crie uma única resposta coesa, amigável e direta para o WhatsApp."
            )
            
            try:
                final_consensus = await asyncio.to_thread(self.gemini.llm.invoke, consensus_prompt)
                return final_consensus.content
            except Exception as e:
                logger.error(f"Erro ao gerar consenso: {e}. Retornando a resposta da IA de maior prioridade.")
                for priority_name in self.priority_order:
                    for s in survivors:
                        if s["name"] == priority_name:
                            return s["content"]
                return survivors[0]["content"]
