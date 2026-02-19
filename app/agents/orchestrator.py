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
        
        history = "\n".join([
            m.content for m in messages 
            if isinstance(m, (HumanMessage, AIMessage)) and hasattr(m, 'content') and m.content
        ])
        
        second_opinion = gemini_svc.get_second_opinion(
            original_plan=last_ai_message,
            real_tips=history
        )
        
        refined = f"{last_ai_message}\n\n---\n✨ **Segunda Opinião do Especialista (Gemini):**\n{second_opinion}"
        
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
