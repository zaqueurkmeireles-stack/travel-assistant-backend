"""
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
    
    # Adicionar instrução de sistema
    from langchain_core.messages import SystemMessage
    system_prompt = (
        "Você é o TravelCompanion AI, o melhor concierge de viagens do mundo.\n"
        "Sua missão é ajudar o usuário e sua família com informações precisas e proativas.\n"
        "Você tem acesso a documentos de viagem do usuário via ferramenta 'query_travel_documents'.\n"
        "Sempre verifique os documentos se o usuário perguntar sobre suas reservas, voos, hotéis ou seguros.\n"
        "Seja cordial, eficiente e econômico com os dados do usuário (prefira instruções em texto antes de sugerir mapas online).\n"
        "Se o usuário enviar uma localização, use as ferramentas de mapas para orientá-lo."
    )
    
    messages_to_invoke = [SystemMessage(content=system_prompt)] + state["messages"]
    response = llm_with_tools.invoke(messages_to_invoke)
    
    needs_review = not (hasattr(response, "tool_calls") and response.tool_calls)
    
    return {
        "messages": [response],
        "needs_gemini_review": needs_review
    }

def expert_consensus_review(state: AgentState):
    """Nó de Consenso: Aciona Gemini e Claude para revisar respostas complexas"""
    logger.info("🧠 Acionando revisão por Consenso de Especialistas...")
    
    try:
        messages = state["messages"]
        last_ai_message = None
        user_query = ""
        
        for msg in reversed(messages):
            if isinstance(msg, AIMessage) and msg.content and not last_ai_message:
                last_ai_message = msg.content
            if isinstance(msg, HumanMessage) and msg.content and not user_query:
                user_query = msg.content
        
        if not last_ai_message or len(last_ai_message) < 150:
            return {"messages": [], "needs_gemini_review": False}
            
        final_response = last_ai_message
        gemini_opinion = ""

        # 1. Obter opinião do Gemini
        if settings.GOOGLE_GEMINI_API_KEY:
            try:
                from app.services.gemini_service import GeminiService
                gemini_svc = GeminiService()
                gemini_opinion = gemini_svc.get_second_opinion(last_ai_message, user_query)
                logger.info("✅ Opinião do Gemini obtida.")
            except Exception as e:
                logger.error(f"Erro no Gemini: {e}")

        # 2. Obter refinamento final do Claude (Veredito)
        if settings.ANTHROPIC_API_KEY:
            try:
                from app.services.claude_service import ClaudeService
                claude_svc = ClaudeService()
                final_response = claude_svc.get_refined_answer(user_query, last_ai_message, gemini_opinion)
                logger.info("✅ Veredito final do Claude obtido.")
            except Exception as e:
                logger.error(f"Erro no Claude: {e}")
        elif gemini_opinion:
            final_response = f"{last_ai_message}\n\n---\n✨ **Revisão Técnica (Gemini):**\n{gemini_opinion}"

        return {"messages": [AIMessage(content=final_response)], "needs_gemini_review": False}
        
    except Exception as e:
        logger.error(f"Erro no Expert Review: {e}")
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
        logger.info("➡️ Roteando para Expert Consensus Review...")
        return "expert_review"
    
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
    workflow.add_node("expert_review", expert_consensus_review)
    
    workflow.set_entry_point("agent")
    
    workflow.add_conditional_edges(
        "agent",
        route_after_agent,
        {
            "tools": "tools",
            "expert_review": "expert_review",
            "end": END
        }
    )
    
    workflow.add_edge("tools", "agent")
    workflow.add_edge("expert_review", END)
    
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
