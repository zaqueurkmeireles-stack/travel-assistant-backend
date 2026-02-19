"""
OpenAI Service - Integração com GPT-4
"""

from openai import OpenAI
from app.config import settings
from loguru import logger
from typing import Optional, List, Dict
import json

class OpenAIService:
    """Service para integração com OpenAI GPT-4"""
    
    def __init__(self):
        """Inicializa o cliente OpenAI"""
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-4o-mini"
        logger.info("✅ OpenAI Service inicializado")
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        response_format: Optional[Dict] = None
    ) -> str:
        """
        Envia mensagens para o GPT-4 e retorna resposta
        """
        try:
            kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            if response_format:
                kwargs["response_format"] = response_format

            response = self.client.chat.completions.create(**kwargs)
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Erro ao chamar OpenAI: {e}")
            return f"Erro ao processar: {str(e)}"
    
    def generate_travel_recommendation(self, destination: str, preferences: str) -> str:
        """Gera recomendações de viagem iniciais"""
        messages = [
            {
                "role": "system",
                "content": "Você é um assistente especializado em viagens. Forneça dicas úteis e personalizadas."
            },
            {
                "role": "user",
                "content": f"Destino: {destination}\nPreferências: {preferences}\nMe dê 5 dicas essenciais!"
            }
        ]
        return self.chat_completion(messages, temperature=0.8)
    
    def analyze_document(self, text: str, document_type: str) -> Dict:
        """Analisa documento extraído e retorna dados estruturados"""
        messages = [
            {
                "role": "system",
                "content": f"Extraia informações estruturadas deste documento de {document_type}. Retorne estritamente em JSON."
            },
            {
                "role": "user",
                "content": text
            }
        ]
        response = self.chat_completion(messages, temperature=0.1, response_format={"type": "json_object"})
        try:
            return json.loads(response)
        except Exception:
            return {"extracted_data": response}

    def analyze_expense(self, expense_text: str) -> Dict:
        """
        Extrai valor e categoria de um gasto enviado pelo usuário
        Útil para atualizar dinamicamente o balance e drawdown da viagem.
        """
        messages = [
            {
                "role": "system",
                "content": "Você é um assistente financeiro de viagem. Extraia a despesa do texto fornecido. Retorne estritamente JSON com as chaves: 'amount' (float), 'currency' (str), 'category' (str), 'description' (str)."
            },
            {
                "role": "user",
                "content": expense_text
            }
        ]
        response = self.chat_completion(messages, temperature=0.1, response_format={"type": "json_object"})
        try:
            return json.loads(response)
        except Exception as e:
            logger.error(f"Erro no parse de despesa: {e}")
            return {"amount": 0.0, "currency": "BRL", "category": "unknown", "description": expense_text}
