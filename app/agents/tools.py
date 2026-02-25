"""
Tools - Ferramentas disponíveis para o agente LangGraph
"""

from langchain.tools import tool
from app.services.openai_service import OpenAIService
from app.services.maps_service import GoogleMapsService
from app.services.weather_service import WeatherService
from app.services.flights_service import FlightsService
from app.services.search_service import SearchService
from app.services.rag_service import RAGService
from loguru import logger

# Lazy initialization para evitar erros de ordem de importação
_openai_svc = None
_maps_svc = None
_weather_svc = None
_flights_svc = None
_search_svc = None
_rag_svc = None

def get_openai_svc():
    global _openai_svc
    if _openai_svc is None:
        _openai_svc = OpenAIService()
    return _openai_svc

def get_maps_svc():
    global _maps_svc
    if _maps_svc is None:
        _maps_svc = GoogleMapsService()
    return _maps_svc

def get_weather_svc():
    global _weather_svc
    if _weather_svc is None:
        _weather_svc = WeatherService()
    return _weather_svc

def get_flights_svc():
    global _flights_svc
    if _flights_svc is None:
        _flights_svc = FlightsService()
    return _flights_svc

def get_search_svc():
    global _search_svc
    if _search_svc is None:
        _search_svc = SearchService()
    return _search_svc

def get_rag_svc():
    global _rag_svc
    if _rag_svc is None:
        _rag_svc = RAGService()
    return _rag_svc

@tool
def get_travel_recommendations(destination: str, preferences: str) -> str:
    """Obtém recomendações personalizadas de viagem para um destino."""
    logger.info(f"🎯 Tool: Recomendações para {destination}")
    return get_openai_svc().generate_travel_recommendation(destination, preferences)

@tool
def get_current_weather(city: str, country_code: str = "") -> str:
    """Obtém o clima atual de uma cidade."""
    logger.info(f"🌤️ Tool: Clima em {city}")
    weather = get_weather_svc().get_current_weather(city, country_code)
    
    if weather:
        return f"Clima em {weather['city']}, {weather['country']}: {weather['temperature']}°C, {weather['description']}. Sensação: {weather['feels_like']}°C, Umidade: {weather['humidity']}%"
    return f"Não foi possível obter clima para {city}"

@tool
def get_flight_status(flight_number: str, date: str = "") -> str:
    """Verifica o status de um voo."""
    logger.info(f"✈️ Tool: Status do voo {flight_number}")
    flight = get_flights_svc().get_flight_status(flight_number, date if date else None)
    
    if flight:
        return f"Voo {flight['flight_number']} ({flight['airline']}): {flight['departure_airport']} -> {flight['arrival_airport']}. Status: {flight['status']}. Partida: {flight['departure_time']}, Chegada: {flight['arrival_time']}"
    return f"Não foi possível obter status do voo {flight_number}"

@tool
def find_nearby_places(city: str, place_type: str = "restaurant") -> str:
    """Busca lugares próximos em uma cidade."""
    logger.info(f"🗺️ Tool: Buscando {place_type} em {city}")
    location = get_maps_svc().geocode(city)
    if not location:
        return f"Não foi possível encontrar localização de {city}"
    
    places = get_maps_svc().find_nearby_places(location['lat'], location['lng'], place_type)
    
    if places:
        result = f"Top lugares ({place_type}) em {city}:\n"
        for i, place in enumerate(places, 1):
            result += f"{i}. {place['name']} - Avaliação: {place['rating']} - {place['address']}\n"
        return result
    return f"Não foram encontrados lugares do tipo {place_type} em {city}"

@tool
def search_real_travel_tips(destination: str, topic: str = "dicas e experiências") -> str:
    """Busca dicas reais de viajantes na internet (fóruns, blogs, Reddit)."""
    logger.info(f"🌐 Tool: Buscando experiências reais sobre {destination}")
    return get_search_svc().search_real_experiences(destination, topic)

@tool
def get_directions(origin: str, destination: str, mode: str = "driving") -> str:
    """Obtém direções entre dois lugares."""
    logger.info(f"🚗 Tool: Direções de {origin} para {destination}")
    directions = get_maps_svc().get_directions(origin, destination, mode)
    
    if directions:
        return f"Rota de {directions['start_address']} para {directions['end_address']}: Distância: {directions['distance']}, Duração: {directions['duration']}"
    return f"Não foi possível calcular rota de {origin} para {destination}"

@tool
def register_expense(expense_text: str) -> str:
    """Registra um gasto financeiro da viagem na variação do balance/drawdown."""
    logger.info(f"💸 Tool: Registrando despesa: {expense_text}")
    result = get_openai_svc().analyze_expense(expense_text)
    return f"Despesa registrada: {result['amount']} {result['currency']} (Categoria: {result['category']})."

from langchain_core.runnables import RunnableConfig

@tool
def query_travel_documents(query_text: str, config: RunnableConfig) -> str:
    """
    Busca informações em documentos pessoais de viagem (passagens, hotéis, seguros) 
    armazenados na memória (RAG). Use quando o usuário perguntar detalhes específicos 
    de sua própria viagem.
    """
    thread_id = config.get("configurable", {}).get("thread_id", "default")
    logger.info(f"📂 Tool: Consultando documentos (Thread: {thread_id})")
    return get_rag_svc().query(query_text, thread_id)

# Lista completa de tools
ALL_TOOLS = [
    get_travel_recommendations,
    get_current_weather,
    get_flight_status,
    find_nearby_places,
    search_real_travel_tips,
    get_directions,
    register_expense,
    query_travel_documents
]
