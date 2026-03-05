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
_emergency_svc = None
_park_svc = None
_event_svc = None

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

def get_emergency_svc():
    global _emergency_svc
    if _emergency_svc is None:
        from app.services.emergency_service import EmergencyService
        _emergency_svc = EmergencyService()
    return _emergency_svc

def get_park_svc():
    global _park_svc
    if _park_svc is None:
        from app.services.park_service import ParkService
        _park_svc = ParkService()
    return _park_svc

def get_event_svc():
    global _event_svc
    if _event_svc is None:
        from app.services.event_service import EventService
        _event_svc = EventService()
    return _event_svc

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
def list_travel_documents(config: RunnableConfig, category: str = None) -> str:
    """
    Lista os documentos de viagem salvos. 
    Opcionalmente filtre por categoria (ex: 'passagem', 'hotel', 'seguro', 'parque', 'carro', 'roteiro').
    Use quando o usuário perguntar 'quais passagens tenho?' ou 'liste meus ingressos'.
    """
    thread_id = config.get("configurable", {}).get("thread_id", "default")
    logger.info(f"📂 Tool: Listando documentos (Thread: {thread_id}, Filtro: {category})")
    
    # Mapeamento amigável
    cat_map = {
        "passagens": "passagem",
        "bilhetes": "passagem",
        "voos": "passagem",
        "hoteis": "hotel",
        "hospedagem": "hotel",
        "ingressos": "parque",
        "tickets": "parque",
        "shoppings": "shopping"
    }
    document_type = cat_map.get(category.lower()) if category else category
    
    docs = get_rag_svc().list_user_documents(thread_id, document_type=document_type)
    if not docs:
        return f"Nenhum documento encontrado para a categoria '{category or 'geral'}'. "
    return "Documentos salvos:\n- " + "\n- ".join(docs)

@tool
def confirm_document_replacement(config: RunnableConfig) -> str:
    """
    Confirma a substituição de um documento que estava em conflito.
    Chame quando o usuário responder 'sim', 'pode substituir' ou 'confirmo'.
    """
    thread_id = config.get("configurable", {}).get("thread_id", "default")
    from app.services.user_service import UserService
    user_svc = UserService()
    
    pending = user_svc.get_pending_substitution(thread_id)
    if not pending:
        return "Não encontrei nenhuma substituição pendente."
    
    from app.services.rag_service import RAGService
    rag = RAGService()
    
    # 1. Remover o antigo (mesmo tipo e viajante)
    traveler = pending.get("traveler")
    doc_type = pending.get("document_type")
    trip_id = pending.get("metadata", {}).get("trip_id")
    
    rag.delete_documents_by_type(thread_id, doc_type, trip_id=trip_id, traveler_name=traveler)
    
    # 2. Indexar o novo
    text = pending.get("text")
    metadata = pending.get("metadata")
    
    # Chunking manual se for muito grande
    chunk_size = 4000
    overlap = 200
    if len(text) > chunk_size:
        for i in range(0, len(text), chunk_size - overlap):
            chunk = text[i:i + chunk_size]
            rag.add_document(chunk, metadata)
    else:
        rag.add_document(text, metadata)
    
    user_svc.clear_pending_substitution(thread_id)
    return f"✅ Documento '{pending['filename']}' substituído com sucesso para o passageiro {traveler}!"

@tool
def confirm_irrelevancy_inclusion(config: RunnableConfig) -> str:
    """
    Confirma a inclusão de um documento que foi inicialmente marcado como irrelevante.
    Chame quando o usuário responder 'sim', 'pode incluir' ou 'tenho certeza'.
    """
    thread_id = config.get("configurable", {}).get("thread_id", "default")
    from app.services.user_service import UserService
    user_svc = UserService()
    
    pending = user_svc.get_pending_irrelevancy(thread_id)
    if not pending:
        return "Não encontrei nenhum documento irrelevante pendente de inclusão."
    
    from app.services.rag_service import RAGService
    rag = RAGService()
    
    text = pending.get("text")
    metadata = pending.get("metadata")
    
    # Chunking manual se for muito grande
    chunk_size = 4000
    overlap = 200
    if len(text) > chunk_size:
        for i in range(0, len(text), chunk_size - overlap):
            chunk = text[i:i + chunk_size]
            rag.add_document(chunk, metadata)
    else:
        rag.add_document(text, metadata)
    
    user_svc.clear_pending_irrelevancy(thread_id)
    return f"✅ Documento '{pending.get('filename', 'documento')}' incluído no dossiê de viagem com sucesso!"

@tool
def discard_pending_action(config: RunnableConfig) -> str:
    """
    Descarta qualquer ação pendente de substituição ou inclusão de documento irrelevante.
    Chame quando o usuário responder 'não', 'cancela', 'esquece' ou similar.
    """
    thread_id = config.get("configurable", {}).get("thread_id", "default")
    from app.services.user_service import UserService
    user_svc = UserService()
    
    user_svc.clear_pending_substitution(thread_id)
    user_svc.clear_pending_irrelevancy(thread_id)
    
    return "Ação cancelada. O documento anterior foi mantido ou a nova inclusão foi descartada."

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
def diagnostic_rag(config: RunnableConfig) -> str:
    """
    Ferramenta de diagnóstico técnico para verificar se os documentos estão corretamente vinculados.
    Use quando o administrador disser algo como 'debug rag' ou 'diagnostico'.
    """
    thread_id = config.get("configurable", {}).get("thread_id", "default")
    rag = get_rag_svc()
    from app.services.user_service import UserService
    us = UserService()
    norm_id = us.normalize_phone(thread_id)
    active_trip = us.get_active_trip(norm_id)
    
    report = [f"--- DIAGNÓSTICO RAG ({thread_id}) ---"]
    report.append(f"ID Normalizado: {norm_id}")
    report.append(f"Viagem Ativa: {active_trip}")
    report.append("\nDocumentos Detectados:")
    
    count = 0
    for doc in rag.documents:
        m = doc["metadata"]
        m_trip = m.get("trip_id")
        m_thread = m.get("thread_id")
        
        # Filtro simplificado do RAG
        if (active_trip and m_trip == active_trip) or us.normalize_phone(m_thread) == norm_id:
            count += 1
            report.append(f"- {m.get('filename')} (Trip: {m_trip} | User: {m_thread})")
            
    if count == 0:
        report.append("Nenhum documento encontrado.")
        
    return "\n".join(report)

@tool
def search_flights(origin: str, destination: str, departure_date: str, return_date: str = "", adults: int = 1, children: int = 0) -> str:
    """
    Busca ofertas de voos REAIS em tempo real, ordenadas pelo menor preço.
    origin/destination: Códigos IATA de 3 letras (ex: GRU para São Paulo, LIS para Lisboa, CDG para Paris).
    departure_date/return_date: Formato YYYY-MM-DD.
    adults: número de adultos (padrão 1).
    children: número de crianças (padrão 0).
    Retorna as 5 melhores ofertas com preço, horários, paradas e ID para reserva.
    """
    logger.info(f"✈️ Tool: Buscando voos {origin}->{destination} | {adults}A+{children}C")
    return get_duffel_svc().search_flights(
        origin, destination, departure_date,
        return_date=return_date if return_date else None,
        adults=adults,
        children=children
    )

@tool
def book_flight(offer_id: str, passenger_name: str, passenger_email: str, birth_date: str) -> str:
    """
    Reserva uma passagem aérea com 1 clique usando o ID da oferta.
    offer_id: ID retornado pela busca (ex: off_0000B3v4lFTez3r3qPTKDa).
    passenger_name: Nome completo do passageiro.
    passenger_email: E-mail para receber a confirmação.
    birth_date: Data de nascimento no formato YYYY-MM-DD.
    """
    logger.info(f"🎫 Tool: Reservando passagem {offer_id[:30]} para {passenger_name}")
    return get_duffel_svc().create_order(offer_id, passenger_name, passenger_email, birth_date)

@tool
def search_government_notices(destination: str, query: str = "") -> str:
    """
    Busca avisos oficiais, alertas de segurança e notícias governamentais para um destino.
    Use para encontrar mudanças em vistos, alertas de saúde ou segurança em sites oficiais (.gov).
    """
    search_query = f"official government travel alerts notices {destination} {query} site:gov"
    logger.info(f"🏛️ Tool: Buscando avisos governamentais para {destination}")
    return get_serpapi_svc().search(search_query)

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
def get_local_emergency_numbers(country: str) -> str:
    """
    Fornece os números de emergência locais (Polícia, Ambulância, Bombeiros) para o país informado.
    Use IMEDIATAMENTE se o usuário reportar um acidente, roubo, emergência médica ou perigo.
    """
    logger.info(f"🚨 Tool: Buscando números de emergência para {country}")
    svc = get_emergency_svc()
    numbers = svc.get_numbers(country)
    return svc.format_emergency_message(country, numbers)

@tool
def get_park_live_status(park_name_or_id: str) -> str:
    """
    Busca o status em tempo real de um parque temático (ex: 'europa_park', 'disneyland_paris').
    Retorna tempos de espera de filas e status das atrações.
    """
    logger.info(f"🎢 Tool: Buscando status do parque {park_name_or_id}")
    svc = get_park_svc()
    live_data = svc.get_live_data(park_name_or_id)
    return svc.format_park_summary(live_data)

@tool
def get_event_venue_details(event_name: str, venue: str) -> str:
    """
    Pesquisa e extrai detalhes cruciais de um local de evento (F1, Shows).
    Busca por: Portões de acesso, localização de banheiros, praças de alimentação e dicas de sobrevivência.
    """
    logger.info(f"🏁 Tool: Pesquisando detalhes de evento: {event_name} em {venue}")
    # O Agente usará busca_web para alimentar essa lógica.
    return f"Pesquisando layouts, portões e instalações para {event_name} em {venue}. Por favor, aguarde enquanto analiso os mapas mais recentes..."

@tool
def generate_social_post(description: str, config: RunnableConfig) -> str:
    """
    Gera opções de legendas e hashtags inteligentes para Instagram/Facebook.
    Use quando o usuário quiser postar uma foto da viagem e precisar de ajuda com o texto.
    """
    user_id = config.get("configurable", {}).get("thread_id", "default")
    from app.services.user_service import UserService
    from app.services.trip_service import TripService
    user_svc = UserService()
    trip_svc = TripService()
    
    active_trip_id = user_svc.get_active_trip(user_id)
    destination = "Viagem Incrível"
    if active_trip_id:
        for t in trip_svc.trips:
            if t["id"] == active_trip_id:
                destination = t["destination"]
                break
                
    openai_svc = get_openai_svc()
    post_ideas = openai_svc.generate_social_caption(destination, description)
    
    return (
        f"📸 **SEU POST ESTÁ PRONTO!** 🤳\n\n"
        f"Aqui estão as melhores opções de legenda para sua foto em **{destination}**:\n\n"
        f"{post_ideas}\n\n"
        f"💡 **Dica do Seven:** Basta copiar sua favorita e colar no Instagram/Facebook!"
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
    from app.services.user_service import UserService
    trip_svc = TripService()
    user_svc = UserService()
    
    if action == "accept":
        # Encontrar a trip associada ao código
        partner_trip_id = None
        for trip in trip_svc.trips:
            if trip.get("confirmation_code") == confirmation_code:
                partner_trip_id = trip["id"]
                break
        
        if partner_trip_id:
            user_svc.link_user_to_trip(user_id, partner_trip_id)
            trip_svc.request_trip_sharing(user_id, confirmation_code, partner_whatsapp)
            # Recíproco
            trip_svc.request_trip_sharing(partner_whatsapp, confirmation_code, user_id)
            return f"✅ Viagem compartilhada com sucesso! Agora você e {partner_whatsapp} compartilham o mesmo dossiê e RAG para esta viagem."
        return "Não consegui encontrar a viagem original para compartilhar."
    
    return f"Solicitação enviada. Aguardando {partner_whatsapp} aceitar."

@tool
def link_with_partner_trip(partner_phone: str, config: RunnableConfig) -> str:
    """
    Vincula o usuário atual à viagem de um parceiro (ex: esposa/marido) para compartilhar o RAG.
    Use quando o usuário disser 'estou viajando com minha esposa' ou fornecer o número do parceiro.
    """
    user_id = config.get("configurable", {}).get("thread_id", "default")
    from app.services.user_service import UserService
    from app.services.trip_service import TripService
    user_svc = UserService()
    trip_svc = TripService()
    
    partner_uid = user_svc.normalize_phone(partner_phone)
    partner_trip_id = user_svc.get_active_trip(partner_uid)
    
    if not partner_trip_id:
        return f"Não encontrei nenhuma viagem ativa vinculada ao número {partner_phone}. Peça para seu parceiro enviar a passagem primeiro!"
        
    user_svc.link_user_to_trip(user_id, partner_trip_id)
    return f"✅ Sucesso! Agora você está vinculado à mesma viagem de {partner_phone}. Seus documentos e informações agora são compartilhados no mesmo cérebro (RAG)."

@tool
def invite_family_member(phone_number: str, config: RunnableConfig) -> str:
    """
    Autoriza e convida um familiar (ex: esposa/marido) para compartilhar os documentos de viagem.
    Use quando o usuário disser 'quero adicionar minha esposa' ou fornecer o número de alguém que viaja junto.
    """
    user_id = config.get("configurable", {}).get("thread_id", "default")
    from app.services.user_service import UserService
    user_svc = UserService()
    
    active_trip_id = user_svc.get_active_trip(user_id)
    if not active_trip_id:
        return "Você precisa ter uma viagem ativa e documentos enviados antes de convidar alguém. Envie sua passagem primeiro!"
        
    partner_uid = user_svc.normalize_phone(phone_number)
    
    # Autoriza o convidado
    user_svc.authorize_guest(user_id, partner_uid, active_trip_id)
    
    return f"✅ Convite processado! O número {phone_number} foi autorizado para acessar o RAG compartilhado da sua viagem para {active_trip_id.split('_')[1]}. Peça para {phone_number} mandar um 'Oi' para o robô!"

@tool
def configure_proactive_frequency(level: str, config: RunnableConfig) -> str:
    """
    Configura a frequência de dicas proativas (lugares, compras, avisos).
    level: 'low' (a cada 6h), 'medium' (a cada 1h), 'high' (a cada 30min).
    Use quando o usuário disser 'quero mais dicas', 'estou explorando' ou similar.
    """
    user_id = config.get("configurable", {}).get("thread_id", "default")
    from app.services.trip_service import TripService
    trip_svc = TripService()
    
    success = trip_svc.update_proactive_config(user_id, level)
    if success:
        freq_desc = {"low": "6 horas", "medium": "1 hora", "high": "30 minutos"}.get(level.lower(), "6 horas")
        return f"✅ Entendido! No 'Modo Ativo', enviarei dicas de gastronomia e atrações a cada {freq_desc}."
    return "Não consegui alterar a frequência. Verifique se você tem uma viagem ativa registrada."

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
    list_travel_documents,
    diagnostic_rag,
    search_flights,
    book_flight,
    search_hotels,
    convert_currency,
    get_internet_options,
    register_data_plan,
    get_data_usage_status,
    analyze_data_usage_screenshot,
    provide_visual_navigation_map,
    manage_trip_sharing,
    get_local_emergency_numbers,
    generate_social_post,
    get_park_live_status,
    get_event_venue_details,
    search_government_notices,
    configure_proactive_frequency,
    confirm_document_replacement,
    confirm_irrelevancy_inclusion,
    discard_pending_action,
    link_with_partner_trip,
    invite_family_member
]
