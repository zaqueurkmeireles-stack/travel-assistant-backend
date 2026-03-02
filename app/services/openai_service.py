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
    
    def analyze_text(self, text: str, system_prompt: str = "Você é um assistente útil especializado em viagens.") -> str:
        """Versão simplificada para análise de texto puro"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text}
        ]
        return self.chat_completion(messages)

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
                "content": (
                    f"Você é um especialista em processamento de documentos de viagem ({document_type}).\n"
                    "Extraia as informações estruturadas e responda APENAS com um objeto JSON.\n"
                    "Campos obrigatórios se encontrados:\n"
                    "- 'destination': Cidade ou país de destino.\n"
                    "- 'start_date': Data de início/partida no formato YYYY-MM-DD.\n"
                    "- 'end_date': Data de término/retorno no formato YYYY-MM-DD.\n"
                    "- 'travelers': Lista de nomes de viajantes.\n"
                    "- 'confirmation_code': Código de reserva ou localizador.\n"
                    "- 'flight_number': Número do voo (ex: LA3211, TP186).\n"
                    "- 'terminal': Terminal de embarque/desembarque (se disponível).\n"
                    "- 'checkin_counter': Guichê ou balcão de check-in (se disponível).\n"
                    "- 'event_name': Nome do evento se for ticket de show/F1.\n"
                    "- 'venue': Local do evento ou atração específica.\n"
                    "- 'gate': Portão de acesso (para eventos).\n"
                    "- 'points_of_interest': Lista de lugares ou atrações mencionadas (ex: ['Torrey Pines State Park', 'USS Midway']).\n"
                    "- 'summary': Breve resumo do documento.\n"
                    "- 'is_travel_content': Booleano. True se o documento for claramente relacionado a viagem (passagem, hotel, ticket de parque, seguro, boucher de carro, roteiro) e False se for algo sem relação (receita, documento pessoal sem viagem, notícia, etc)."
                )
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

    def generate_social_caption(self, destination: str, description: str) -> str:
        """Gera 3 opções de legendas (Criativa, Poética, Informativa) + Hashtags"""
        messages = [
            {
                "role": "system", 
                "content": "Você é um Social Media Manager de viagens de luxo. Gere 3 opções de legendas para Instagram/Facebook (Curta e impactante, Poética/Inspiradora e Informativa com dicas). Inclua emojis e 5-8 hashtags relevantes."
            },
            {
                "role": "user", 
                "content": f"Foto tirada em: {destination}\nDescrição da cena: {description}"
            }
        ]
        return self.chat_completion(messages, temperature=0.8)

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
