"""
TravelCompanion AI - Criação Automática de Services
Executa: python create_services.py
"""

import os
from pathlib import Path

FILES = {}

# ============================================================
# OPENAI SERVICE
# ============================================================
FILES["app/services/openai_service.py"] = '''"""
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
                "content": f"Destino: {destination}\\nPreferências: {preferences}\\nMe dê 5 dicas essenciais!"
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
'''

# ============================================================
# GEMINI SERVICE (NOVO)
# ============================================================
FILES["app/services/gemini_service.py"] = '''"""
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
            "Você é um consultor de viagens experiente e pragmático.\\n"
            f"Plano Original:\\n{original_plan}\\n\\n"
            f"Relatos reais de quem já foi (Internet):\\n{real_tips}\\n\\n"
            "Com base nos relatos reais, aponte potenciais pegadinhas, ajuste o roteiro "
            "e traga uma resposta robusta melhorando a ideia original."
        )
        
        try:
            response = self.llm.invoke(prompt)
            return response.content
        except Exception as e:
            logger.error(f"Erro ao consultar Gemini: {e}")
            return f"Erro na análise secundária: {str(e)}"
'''

# ============================================================
# SEARCH SERVICE (NOVO)
# ============================================================
FILES["app/services/search_service.py"] = '''"""
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
                results = "\\n".join([f"- {res['title']}: {res['content'][:200]}..." for res in data.get("results", [])])
                return f"Resumo da Comunidade:\\n{answer}\\n\\nFontes Diretas:\\n{results}"
            else:
                logger.error(f"Erro Tavily: {data}")
                return "Erro ao processar buscas na internet."
                
        except Exception as e:
            logger.error(f"Erro no SearchService: {e}")
            return "Falha de conexão ao buscar experiências."
'''

# ============================================================
# GOOGLE MAPS SERVICE
# ============================================================
FILES["app/services/maps_service.py"] = '''"""
Google Maps Service - Geocoding e busca de lugares
"""

import requests
from app.config import settings
from loguru import logger
from typing import Optional, Dict, List

class GoogleMapsService:
    """Service para integração com Google Maps API"""
    
    def __init__(self):
        """Inicializa o service"""
        self.api_key = settings.GOOGLE_MAPS_API_KEY
        self.base_url = "https://maps.googleapis.com/maps/api"
        logger.info("✅ Google Maps Service inicializado")
    
    def geocode(self, address: str) -> Optional[Dict]:
        """Converte endereço em coordenadas"""
        try:
            url = f"{self.base_url}/geocode/json"
            params = {
                "address": address,
                "key": self.api_key
            }
            
            response = requests.get(url, params=params, timeout=15)
            data = response.json()
            
            if data["status"] == "OK":
                location = data["results"][0]["geometry"]["location"]
                return {
                    "lat": location["lat"],
                    "lng": location["lng"],
                    "formatted_address": data["results"][0]["formatted_address"]
                }
            else:
                logger.warning(f"Geocode falhou: {data['status']}")
                return None
                
        except Exception as e:
            logger.error(f"Erro no geocode: {e}")
            return None
    
    def find_nearby_places(self, lat: float, lng: float, place_type: str = "restaurant", radius: int = 1500) -> List[Dict]:
        """Busca lugares próximos"""
        try:
            url = f"{self.base_url}/place/nearbysearch/json"
            params = {
                "location": f"{lat},{lng}",
                "radius": radius,
                "type": place_type,
                "key": self.api_key
            }
            
            response = requests.get(url, params=params, timeout=15)
            data = response.json()
            
            if data["status"] == "OK":
                places = []
                for place in data["results"][:5]:  # Top 5
                    places.append({
                        "name": place.get("name"),
                        "address": place.get("vicinity"),
                        "rating": place.get("rating", "N/A"),
                        "types": place.get("types", [])
                    })
                return places
            else:
                logger.warning(f"Busca de lugares falhou: {data['status']}")
                return []
                
        except Exception as e:
            logger.error(f"Erro ao buscar lugares: {e}")
            return []
    
    def get_directions(self, origin: str, destination: str, mode: str = "driving") -> Optional[Dict]:
        """Obtém direções entre dois pontos"""
        try:
            url = f"{self.base_url}/directions/json"
            params = {
                "origin": origin,
                "destination": destination,
                "mode": mode,
                "key": self.api_key
            }
            
            response = requests.get(url, params=params, timeout=15)
            data = response.json()
            
            if data["status"] == "OK":
                route = data["routes"][0]["legs"][0]
                return {
                    "distance": route["distance"]["text"],
                    "duration": route["duration"]["text"],
                    "start_address": route["start_address"],
                    "end_address": route["end_address"]
                }
            else:
                logger.warning(f"Direções falharam: {data['status']}")
                return None
                
        except Exception as e:
            logger.error(f"Erro ao obter direções: {e}")
            return None
'''

# ============================================================
# WEATHER SERVICE
# ============================================================
FILES["app/services/weather_service.py"] = '''"""
OpenWeather Service - Previsão do tempo
"""

import requests
from app.config import settings
from loguru import logger
from typing import Optional, Dict, List

class WeatherService:
    """Service para integração com OpenWeather API"""
    
    def __init__(self):
        """Inicializa o service"""
        self.api_key = settings.OPENWEATHER_API_KEY
        self.base_url = "https://api.openweathermap.org/data/2.5"
        logger.info("✅ Weather Service inicializado")
    
    def get_current_weather(self, city: str, country_code: str = "") -> Optional[Dict]:
        """Obtém clima atual de uma cidade"""
        try:
            location = f"{city},{country_code}" if country_code else city
            url = f"{self.base_url}/weather"
            params = {
                "q": location,
                "appid": self.api_key,
                "units": "metric",  # Celsius
                "lang": "pt_br"
            }
            
            response = requests.get(url, params=params, timeout=15)
            data = response.json()
            
            if response.status_code == 200:
                return {
                    "temperature": round(data["main"]["temp"]),
                    "feels_like": round(data["main"]["feels_like"]),
                    "humidity": data["main"]["humidity"],
                    "description": data["weather"][0]["description"],
                    "wind_speed": data["wind"]["speed"],
                    "city": data["name"],
                    "country": data["sys"]["country"]
                }
            else:
                logger.warning(f"Erro ao buscar clima: {data.get('message')}")
                return None
                
        except Exception as e:
            logger.error(f"Erro no WeatherService: {e}")
            return None
    
    def get_forecast(self, city: str, days: int = 5) -> Optional[List[Dict]]:
        """Obtém previsão do tempo para os próximos dias"""
        try:
            url = f"{self.base_url}/forecast"
            params = {
                "q": city,
                "appid": self.api_key,
                "units": "metric",
                "lang": "pt_br",
                "cnt": days * 8  # API retorna previsões de 3h em 3h
            }
            
            response = requests.get(url, params=params, timeout=15)
            data = response.json()
            
            if response.status_code == 200:
                forecasts = []
                for item in data["list"][::8]:  # Pegar 1 por dia
                    forecasts.append({
                        "date": item["dt_txt"],
                        "temperature": round(item["main"]["temp"]),
                        "description": item["weather"][0]["description"],
                        "humidity": item["main"]["humidity"]
                    })
                return forecasts
            else:
                logger.warning(f"Erro ao buscar previsão: {data.get('message')}")
                return None
                
        except Exception as e:
            logger.error(f"Erro ao buscar previsão: {e}")
            return None
'''

# ============================================================
# FLIGHTS SERVICE
# ============================================================
FILES["app/services/flights_service.py"] = '''"""
Flights Service - Monitoramento de voos (AeroDataBox)
"""

import requests
from app.config import settings
from loguru import logger
from typing import Optional, Dict
from datetime import datetime

class FlightsService:
    """Service para monitoramento de voos"""
    
    def __init__(self):
        """Inicializa o service"""
        self.api_key = settings.AERODATABOX_API_KEY
        self.api_host = settings.AERODATABOX_API_HOST
        self.base_url = f"https://{self.api_host}/flights"
        logger.info("✅ Flights Service inicializado")
    
    def get_flight_status(self, flight_number: str, date: str = None) -> Optional[Dict]:
        """Obtém status de um voo"""
        if not self.api_key:
            logger.warning("AeroDataBox API key não configurada")
            return self._mock_flight_status(flight_number)
        
        try:
            if date is None:
                date = datetime.now().strftime("%Y-%m-%d")
            
            url = f"{self.base_url}/number/{flight_number}/{date}"
            headers = {
                "X-RapidAPI-Key": self.api_key,
                "X-RapidAPI-Host": self.api_host
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            data = response.json()
            
            if response.status_code == 200 and len(data) > 0:
                flight = data[0]
                return {
                    "flight_number": flight.get("number"),
                    "airline": flight.get("airline", {}).get("name"),
                    "departure_airport": flight.get("departure", {}).get("airport", {}).get("iata"),
                    "arrival_airport": flight.get("arrival", {}).get("airport", {}).get("iata"),
                    "status": flight.get("status"),
                    "departure_time": flight.get("departure", {}).get("scheduledTime", {}).get("local"),
                    "arrival_time": flight.get("arrival", {}).get("scheduledTime", {}).get("local")
                }
            else:
                logger.warning(f"Voo não encontrado: {flight_number}")
                return None
                
        except Exception as e:
            logger.error(f"Erro ao buscar voo: {e}")
            return self._mock_flight_status(flight_number)
    
    def _mock_flight_status(self, flight_number: str) -> Dict:
        """Retorna dados mock para testes"""
        return {
            "flight_number": flight_number,
            "airline": "LATAM Airlines",
            "departure_airport": "GRU",
            "arrival_airport": "GIG",
            "status": "On Time",
            "departure_time": "2026-04-13T10:00:00",
            "arrival_time": "2026-04-13T11:30:00",
            "note": "Dados simulados"
        }
'''

# ============================================================
# WHATSAPP SERVICE
# ============================================================
FILES["app/services/whatsapp_service.py"] = '''"""
WhatsApp Service - Envio de mensagens via WhatsApp Business API
"""

import requests
from app.config import settings
from loguru import logger
from typing import Optional

class WhatsAppService:
    """Service para envio de mensagens WhatsApp"""
    
    def __init__(self):
        """Inicializa o service"""
        self.token = settings.WHATSAPP_TOKEN
        self.phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID
        self.base_url = "https://graph.facebook.com/v18.0"
        
        if not self.token or not self.phone_number_id:
            logger.warning("⚠️ WhatsApp não configurado (modo simulação)")
        else:
            logger.info("✅ WhatsApp Service inicializado")
    
    def send_message(self, to: str, message: str) -> bool:
        """Envia mensagem de texto"""
        if not self.token or not self.phone_number_id:
            logger.info(f"[SIMULADO] Mensagem para {to}: {message}")
            return True
        
        try:
            url = f"{self.base_url}/{self.phone_number_id}/messages"
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
            data = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": "text",
                "text": {"body": message}
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=15)
            
            if response.status_code == 200:
                logger.info(f"✅ Mensagem enviada para {to}")
                return True
            else:
                logger.error(f"Erro ao enviar mensagem: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Erro no WhatsAppService: {e}")
            return False
    
    def send_location(self, to: str, latitude: float, longitude: float, name: str, address: str) -> bool:
        """Envia localização"""
        if not self.token or not self.phone_number_id:
            logger.info(f"[SIMULADO] Localização para {to}: {name} ({latitude}, {longitude})")
            return True
        
        try:
            url = f"{self.base_url}/{self.phone_number_id}/messages"
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
            data = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": "location",
                "location": {
                    "latitude": latitude,
                    "longitude": longitude,
                    "name": name,
                    "address": address
                }
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=15)
            
            if response.status_code == 200:
                logger.info(f"✅ Localização enviada para {to}")
                return True
            else:
                logger.error(f"Erro ao enviar localização: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao enviar localização: {e}")
            return False
'''

# ============================================================
# ATUALIZAR __init__.py DOS SERVICES
# ============================================================
FILES["app/services/__init__.py"] = '''"""Services - Integrações com APIs externas"""

from .openai_service import OpenAIService
from .gemini_service import GeminiService
from .search_service import SearchService
from .maps_service import GoogleMapsService
from .weather_service import WeatherService
from .flights_service import FlightsService
from .whatsapp_service import WhatsAppService

__all__ = [
    "OpenAIService",
    "GeminiService",
    "SearchService",
    "GoogleMapsService",
    "WeatherService",
    "FlightsService",
    "WhatsAppService"
]
'''

def create_services():
    """Cria todos os arquivos de services"""
    
    print("=" * 70)
    print("📦 CRIANDO SERVICES - INTEGRAÇÕES COM APIs")
    print("=" * 70)
    print()
    
    for filepath, content in FILES.items():
        # Proteção: Garantir que a pasta do arquivo existe antes de gravar
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"   ✅ {filepath}")
    
    print()
    print("=" * 70)
    print("✅ SERVICES CRIADOS COM SUCESSO!")
    print("=" * 70)
    print()
    print("📋 Services implementados:")
    print("   🤖 OpenAI Service - GPT-4 e Controle de Custos")
    print("   🧠 Gemini Service - Debate de Segunda Opinião")
    print("   🌐 Search Service - Pesquisa de Relatos na Internet")
    print("   🗺️  Google Maps Service - Geolocalização")
    print("   🌤️  Weather Service - Clima")
    print("   ✈️  Flights Service - Status de voos")
    print("   📱 WhatsApp Service - Mensagens")
    print()

if __name__ == "__main__":
    create_services()