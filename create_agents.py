"""
TravelCompanion AI - Criação Automática de Agents
Executa: python create_agents.py
"""

import os
from pathlib import Path

FILES = {}

# ============================================================
# TOOLS - Ferramentas do Agente
# ============================================================
FILES["app/agents/tools.py"] = '''"""
Tools - Ferramentas disponíveis para o agente LangGraph
"""

from langchain.tools import tool
from app.services.openai_service import OpenAIService
from app.services.maps_service import GoogleMapsService
from app.services.weather_service import WeatherService
from app.services.flights_service import FlightsService
from app.services.search_service import SearchService
from loguru import logger

# Lazy initialization para evitar erros de ordem de importação
_openai_svc = None
_maps_svc = None
_weather_svc = None
_flights_svc = None
_search_svc = None

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
        result = f"Top lugares ({place_type}) em {city}:\\n"
        for i, place in enumerate(places, 1):
            result += f"{i}. {place['name']} - Avaliação: {place['rating']} - {place['address']}\\n"
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

# Lista completa de tools
ALL_TOOLS = [
    get_travel_recommendations,
    get_current_weather,
    get_flight_status,
    find_nearby_places,
    search_real_travel_tips,
    get_directions,
    register_expense
]
'''

# ============================================================
# ORCHESTRATOR - LangGraph (BLINDADO DUAS VEZES)
# ============================================================
FILES["app/agents/orchestrator.py"] = '''"""
Orchestrator - Orquestração de agentes com LangGraph
"""

from typing import TypedDict, Annotated, Literal
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from app.agents.tools import ALL_TOOLS
from app.config import settings
from loguru import logger

# 🛡️ DEFESA: Versões do LangGraph para add_messages
try:
    from langgraph.graph import add_messages
except ImportError:
    from langgraph.graph.message import add_messages

# ============================================================
# ESTADO DO AGENTE
# ============================================================
class AgentState(TypedDict):
    """Estado compartilhado. O add_messages empilha o histórico e impede amnésia."""
    messages: Annotated[list[BaseMessage], add_messages]
    needs_gemini_review: bool

# ============================================================
# NÓS DO GRAFO
# ============================================================

def call_model(state: AgentState):
    """Nó principal: Chama o GPT-4 com acesso às tools"""
    logger.info("🤖 Acionando OpenAI Agent...")
    
    messages = state["messages"]
    
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        api_key=settings.OPENAI_API_KEY,
        temperature=0.7
    )
    llm_with_tools = llm.bind_tools(ALL_TOOLS)
    
    response = llm_with_tools.invoke(messages)
    
    needs_review = not (hasattr(response, "tool_calls") and response.tool_calls)
    
    return {
        "messages": [response],
        "needs_gemini_review": needs_review
    }

def gemini_review(state: AgentState):
    """Nó de Consenso: Aciona o Gemini para revisar respostas complexas"""
    logger.info("🧠 Acionando revisão do Gemini...")
    
    try:
        from app.services.gemini_service import GeminiService
        gemini_svc = GeminiService()
        
        messages = state["messages"]
        last_ai_message = None
        
        for msg in reversed(messages):
            if isinstance(msg, AIMessage) and msg.content:
                last_ai_message = msg.content
                break
        
        # 🛡️ DEFESA: Retornar o estado completo para não quebrar validação do LangGraph
        if not last_ai_message or len(last_ai_message) < 200:
            logger.info("⏩ Resposta curta, pulando revisão do Gemini.")
            return {"messages": [], "needs_gemini_review": False}
        
        history = "\\n".join([
            m.content for m in messages 
            if isinstance(m, (HumanMessage, AIMessage)) and hasattr(m, 'content') and m.content
        ])
        
        second_opinion = gemini_svc.get_second_opinion(
            original_plan=last_ai_message,
            real_tips=history
        )
        
        refined = f"{last_ai_message}\\n\\n---\\n✨ **Segunda Opinião do Especialista (Gemini):**\\n{second_opinion}"
        
        return {"messages": [AIMessage(content=refined)], "needs_gemini_review": False}
        
    except Exception as e:
        logger.error(f"Erro no Gemini review: {e}")
        return {"messages": [], "needs_gemini_review": False}

def route_after_agent(state: AgentState) -> Literal["tools", "gemini_review", "end"]:
    """Roteamento dinâmico após o agente decidir"""
    messages = state["messages"]
    last_message = messages[-1]
    
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        logger.info("➡️ Roteando para Tools...")
        return "tools"
    
    # 🛡️ DEFESA: Lida graciosamente se a flag não existir no config.py / .env
    dual_ai_enabled = getattr(settings, "ENABLE_DUAL_AI_CONSENSUS", False)
    
    if dual_ai_enabled and state.get("needs_gemini_review", False):
        logger.info("➡️ Roteando para Gemini Review...")
        return "gemini_review"
    
    logger.info("✅ Finalizando Orquestração...")
    return "end"

# ============================================================
# CONSTRUIR GRAFO
# ============================================================

def create_agent_graph():
    """Compila o grafo do LangGraph definindo o fluxo exato"""
    tool_node = ToolNode(ALL_TOOLS)
    workflow = StateGraph(AgentState)
    
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", tool_node)
    workflow.add_node("gemini_review", gemini_review)
    
    workflow.set_entry_point("agent")
    
    workflow.add_conditional_edges(
        "agent",
        route_after_agent,
        {
            "tools": "tools",
            "gemini_review": "gemini_review",
            "end": END
        }
    )
    
    workflow.add_edge("tools", "agent")
    workflow.add_edge("gemini_review", END)
    
    # 🛡️ DEFESA: MemorySaver condicional para não quebrar se módulo mudar
    try:
        from langgraph.checkpoint.memory import MemorySaver
        memory = MemorySaver()
        app = workflow.compile(checkpointer=memory)
        logger.info("✅ Grafo LangGraph compilado COM Motor de Memória Persistente")
    except ImportError:
        logger.warning("⚠️ MemorySaver não encontrado na sua versão do LangGraph. Compilando SEM persistência na sessão.")
        app = workflow.compile()
        
    return app

# ============================================================
# EXECUTOR PRINCIPAL
# ============================================================

class TravelAgent:
    """Agente principal encapsulado"""
    
    def __init__(self):
        self.graph = create_agent_graph()
        logger.info("🚀 TravelAgent inicializado")
        
    def chat(self, user_input: str, thread_id: str = "default_thread") -> str:
        """Processa input com persistência de thread_id entre conversas"""
        logger.info(f"💬 Usuário: {user_input} (Thread: {thread_id})")
        
        config = {"configurable": {"thread_id": thread_id}}
        
        initial_state = {
            "messages": [HumanMessage(content=user_input)],
            "needs_gemini_review": False
        }
        
        result = self.graph.invoke(initial_state, config=config)
        messages = result.get("messages", [])
        
        response = ""
        for msg in reversed(messages):
            if isinstance(msg, AIMessage) and msg.content:
                response = msg.content
                break
                
        logger.info(f"🤖 Agente: {response[:100]}...")
        return response
'''

# ============================================================
# ATUALIZAR __init__.py DOS AGENTS
# ============================================================
FILES["app/agents/__init__.py"] = '''"""Agents - Orquestração com LangGraph"""

from .orchestrator import TravelAgent
from .tools import ALL_TOOLS

__all__ = ["TravelAgent", "ALL_TOOLS"]
'''

def create_agents():
    """Cria todos os arquivos de agents"""
    
    print("=" * 70)
    print("🤖 CRIANDO AGENTS - ORQUESTRAÇÃO COM LANGGRAPH")
    print("=" * 70)
    print()
    
    for filepath, content in FILES.items():
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"   ✅ {filepath}")
    
    print()
    print("=" * 70)
    print("✅ AGENTS CRIADOS COM SUCESSO E TOTALMENTE BLINDADOS!")
    print("=" * 70)

if __name__ == "__main__":
    create_agents()