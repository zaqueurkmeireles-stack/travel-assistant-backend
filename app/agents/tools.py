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
from app.services.duffel_service import DuffelService
from app.services.serpapi_service import SerpApiService
from app.services.finance_service import FinanceService
from app.services.connectivity_service import ConnectivityService
from loguru import logger

# Lazy initialization para evitar erros de ordem de importação
_openai_svc = None
_maps_svc = None
_weather_svc = None
_flights_svc = None
_search_svc = None
_rag_svc = None
_duffel_svc = None
_serpapi_svc = None
_finance_svc = None
_connectivity_svc = None

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

def get_duffel_svc():
    global _duffel_svc
    if _duffel_svc is None:
        _duffel_svc = DuffelService()
    return _duffel_svc

def get_serpapi_svc():
    global _serpapi_svc
    if _serpapi_svc is None:
        _serpapi_svc = SerpApiService()
    return _serpapi_svc

def get_finance_svc():
    global _finance_svc
    if _finance_svc is None:
        _finance_svc = FinanceService()
    return _finance_svc

def get_connectivity_svc():
    global _connectivity_svc
    if _connectivity_svc is None:
        _connectivity_svc = ConnectivityService()
    return _connectivity_svc

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
        info = (
            f"Voo {flight['flight_number']} ({flight['airline']}): {flight['departure_airport']} -> {flight['arrival_airport']}. "
            f"Status: {flight['status']}. "
            f"Partida: {flight['departure_time']}, Chegada: {flight['arrival_time']}. "
        )
        if flight.get("departure_gate"): info += f"Portão Partida: {flight['departure_gate']}. "
        if flight.get("arrival_gate"): info += f"Portão Chegada: {flight['arrival_gate']}. "
        if flight.get("baggage_belt"): info += f"Esteira de Bagagem: {flight['baggage_belt']}."
        return info
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

@tool
def search_flights(origin: str, destination: str, departure_date: str, return_date: str = "") -> str:
    """
    Busca ofertas de voos REAIS em tempo real.
    origin/destination: Códigos IATA de 3 letras (ex: GRU para São Paulo, CDG para Paris).
    departure_date/return_date: Formato YYYY-MM-DD.
    """
    logger.info(f"✈️ Tool: Buscando voos de {origin} para {destination}")
    return get_duffel_svc().search_flights(origin, destination, departure_date, return_date if return_date else None)

@tool
def search_hotels(city: str, check_in_date: str, check_out_date: str) -> str:
    """
    Busca hotéis reais com preços atuais via Google Hotels.
    check_in_date e check_out_date devem estar no formato YYYY-MM-DD.
    """
    logger.info(f"🏨 Tool: Buscando hotéis em {city}")
    return get_serpapi_svc().search_hotels(city, check_in_date, check_out_date)

@tool
def convert_currency(amount: float, from_currency: str, to_currency: str = "BRL") -> str:
    """
    Converte valores entre moedas (ex: USD para BRL, EUR para BRL).
    Use quando o usuário perguntar preços em outra moeda ou quiser saber cotações.
    """
    logger.info(f"💸 Tool: Convertendo {amount} {from_currency} para {to_currency}")
    return get_finance_svc().convert_currency(amount, from_currency, to_currency)

@tool
def get_internet_options(destination: str) -> str:
    """
    Obtém as melhores opções de chip de internet e eSIM para o destino do viajante.
    """
    logger.info(f"📶 Tool: Opções de internet para {destination}")
    return get_connectivity_svc().get_e_sim_recommendations(destination)

@tool
def register_data_plan(total_gb: float, duration_days: int, config: RunnableConfig) -> str:
    """
    Registra um plano de dados (SIM/eSIM) para monitoramento.
    Use quando o usuário disser que comprou um chip ou tiver um plano de X GB por Y dias.
    """
    user_id = config.get("configurable", {}).get("thread_id", "default")
    logger.info(f"📶 Tool: Registrando plano de {total_gb}GB para {user_id}")
    plan = get_rag_svc().trip_svc.register_data_plan(user_id, total_gb, duration_days)
    return f"Perfeito! Registrei seu plano de {total_gb}GB para {duration_days} dias. Vou monitorar seu consumo e te aviso se baixar de 10%!"

@tool
def get_data_usage_status(config: RunnableConfig) -> str:
    """
    Verifica o status atual do consumo de dados (Medidor Virtual).
    Use quando o usuário perguntar 'Quanto de internet eu ainda tenho?' ou similar.
    """
    user_id = config.get("configurable", {}).get("thread_id", "default")
    logger.info(f"📊 Tool: Checando consumo de dados para {user_id}")
    return get_connectivity_svc().estimate_data_usage(user_id)

@tool
def analyze_data_usage_screenshot(image_path: str, config: RunnableConfig) -> str:
    """
    Analisa um print da tela de consumo de dados (eSIM/Chip) para sincronizar o medidor real.
    Use quando o usuário enviar uma imagem das configurações de dados do celular.
    """
    user_id = config.get("configurable", {}).get("thread_id", "default")
    logger.info(f"👁️ Tool: Analisando print de consumo para {user_id}")
    return get_connectivity_svc().analyze_usage_screenshot(user_id, image_path)

@tool
def provide_visual_navigation_map(place_description: str, config: RunnableConfig) -> str:
    """
    Gera um mapa visual e link de navegação para um local específico (ex: 'Esteira de Bagagem 4', 'Hertz Car Rental Terminal 1').
    Use quando o usuário estiver perdido ou precisar chegar a um ponto específico da viagem.
    """
    from app.services.maps_service import GoogleMapsService
    maps = GoogleMapsService()
    
    # 1. Link de navegação real
    link = maps.get_location_map_link(place_description)
    
    # 2. Tentar geocodificar para obter um mapa estático (economia de dados)
    static_map_section = ""
    location = maps.geocode(place_description)
    if location:
        static_url = maps.get_static_map_url(location['lat'], location['lng'])
        static_map_section = f"🖼️ **Mapa de Visualização Rápida (Economia de Dados):**\n{static_url}\n\n"
    
    return (
        f"🗺️ **Guia de Navegação: {place_description}**\n\n"
        f"{static_map_section}"
        f"Clique no link abaixo para abrir a navegação passo a passo:\n"
        f"🔗 [ABRIR NO GOOGLE MAPS]({link})\n\n"
        f"💡 **Dica de Viagem:** Para economizar dados, você pode carregar este mapa agora enquanto tem internet ou baixar a área offline no Google Maps (Menu -> Mapas Offline)."
    )

@tool
def manage_trip_sharing(action: str, partner_whatsapp: str, confirmation_code: str, config: RunnableConfig) -> str:
    """
    Gerencia o compartilhamento de viagens entre usuários.
    Ações: 'request' (enviar convite), 'accept' (aceitar convite).
    Use quando detectar que dois usuários têm o mesmo código de reserva e perguntar se querem compartilhar.
    """
    user_id = config.get("configurable", {}).get("thread_id", "default")
    from app.services.trip_service import TripService
    trip_svc = TripService()
    
    if action == "accept":
        trip_svc.request_trip_sharing(user_id, confirmation_code, partner_whatsapp)
        # Recíproco
        trip_svc.request_trip_sharing(partner_whatsapp, confirmation_code, user_id)
        return f"✅ Viagem compartilhada com sucesso! Agora você e {partner_whatsapp} podem acessar os documentos um do outro para esta viagem."
    
    return f"Solicitação enviada. Aguardando {partner_whatsapp} aceitar."

# Lista completa de tools
ALL_TOOLS = [
    get_travel_recommendations,
    get_current_weather,
    get_flight_status,
    find_nearby_places,
    search_real_travel_tips,
    get_directions,
    register_expense,
    query_travel_documents,
    search_flights,
    search_hotels,
    convert_currency,
    get_internet_options,
    register_data_plan,
    get_data_usage_status,
    analyze_data_usage_screenshot,
    provide_visual_navigation_map,
    manage_trip_sharing
]
