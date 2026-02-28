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
from app.services.n8n_service import N8nService
from app.agents.tools import ALL_TOOLS, provide_visual_navigation_map

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

def call_model(state: AgentState, config: dict = None):
    """Nó principal: Chama o GPT-4 com acesso às tools"""
    logger.info("🤖 Acionando OpenAI Agent...")
    
    messages = state["messages"]
    
    # Recupera o thread_id e injeta o contexto da viagem
    thread_id = "unknown"
    if config and "configurable" in config:
        thread_id = config["configurable"].get("thread_id", "unknown")
    
    from app.services.user_service import UserService
    user_service = UserService()
    role = user_service.get_user_role(thread_id)
    active_trip = user_service.get_active_trip(thread_id)
    
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        api_key=settings.OPENAI_API_KEY,
        temperature=0.7
    )
    llm_with_tools = llm.bind_tools(ALL_TOOLS)
    
    # Adicionar instrução de sistema
    from langchain_core.messages import SystemMessage
    base_prompt = (
        "Voce e o Seven Assistant Travel, o melhor concierge de viagens do mundo. "
        "REGRA ABSOLUTA: Sempre que o usuario perguntar sobre VOO, HORARIO, PASSAGEM, HOTEL, DESTINO, RESERVA, CHECK-IN, CHECK-OUT, SEGURO ou QUALQUER detalhe de viagem, "
        "voce DEVE OBRIGATORIAMENTE chamar a ferramenta 'query_travel_documents' ANTES de responder. "
        "### GUIA DE CHEGADA E AEROPORTO:\n"
        "1. **Malas:** Se o usuário estiver chegando de um voo, procure no RAG ou chame OBRIGATORIAMENTE a ferramenta 'get_flight_status' para verificar a 'Esteira de Bagagem' (baggage_belt). Informe ao usuário onde pegar as malas.\n"
        "2. **Transporte:** Se NÃO houver confirmação de Aluguel de Carro no RAG, pergunte proativamente: 'Como você pretende ir para o hotel? (Carro de aplicativo, Trem, Ônibus ou Uber)'.\n"
        "3. **Busca Proativa:** Se o usuário escolher transporte público (ônibus/trem), use a ferramenta 'search_real_travel_tips' ou 'get_directions' para encontrar o local EXATO do ponto/plataforma no aeroporto.\n"
        "4. **Navegação Real-Time:** Verifique alterações de portão ou atrasos via 'get_flight_status' e use 'provide_visual_navigation_map' para guiar o usuário até o próximo ponto (esteira -> transporte).\n"
        "### PROTOCOLO DE SEGURANÇA E EMERGÊNCIA:\n"
        "- Se o usuário mencionar ACIDENTE, ROUBO, PERIGO, POLÍCIA, AMBULÂNCIA ou palavras de socorro, chame IMEDIATAMENTE 'get_local_emergency_numbers' para o país onde ele está.\n"
        "- Aja com calma e rapidez. Priorize a segurança física do viajante.\n"
        "NUNCA responda de memoria sobre detalhes especificos da viagem do usuario sem antes consultar os documentos via tool. "
        "Se nao ha documentos, peca a passagem primeiro. Analise docs faltantes e cobre carinhosamente. Seja cordial e economico com dados."
    )
    
    context_prompt = f"\n\nContexto Atual:\n- ID Usuário: {thread_id}\n- Seu Papel na Viagem: {role}\n- Viagem Ativa (Trip ID): {active_trip if active_trip else 'Nenhuma viagem vinculada.'}\n"
    context_prompt += "MUITO IMPORTANTE: O usuário pode não ser o dono da viagem, ele pode ser um convidado. A IA deve atender as demandas dessa Viagem Ativa específica."
    
    rag_context = ""
    try:
        from app.services.rag_service import RAGService
        rag = RAGService()
        # Extrai a mensagem mais recente do usuário para busca contextual
        last_user_message = ""
        from langchain_core.messages import HumanMessage
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage) and msg.content:
                last_user_message = msg.content
                break
        
        if last_user_message and rag.documents:
            rag_context = rag.query(last_user_message, thread_id, k=4)
            if rag_context and "ainda não enviou" not in rag_context and "Nenhuma informação" not in rag_context:
                # 🛡️ Super Limite de Segurança (v1.2.3): truncate para 50k chars
                # Isso garante que mesmo com histórico, não estoure os 128k tokens
                if len(rag_context) > 50000:
                    logger.warning(f"⚠️ RAG Context muito grande ({len(rag_context)} chars). Truncando para 50k.")
                    rag_context = rag_context[:50000] + "\n\n[... Contexto truncado por tamanho ...]"
                
                context_prompt += f"\n\n📄 DOCUMENTOS DA VIAGEM (use estas informações para responder):\n{rag_context}"
                logger.info(f"✅ RAG injetado no prompt diretamente ({len(rag_context)} chars)")
            else:
                logger.info("ℹ️ RAG não retornou documentos relevantes para esta consulta.")
    except Exception as rag_err:
        logger.error(f"❌ Erro ao injetar RAG no prompt: {rag_err}")
    
    system_prompt = base_prompt + context_prompt
    
    # ✂️ TRIMMING DE HISTÓRICO: Mantém apenas as últimas 15 mensagens para evitar estouro de tokens
    trimmed_history = messages[-15:] if len(messages) > 15 else messages
    
    messages_to_invoke = [SystemMessage(content=system_prompt)] + trimmed_history
    response = llm_with_tools.invoke(messages_to_invoke)
    
    # 🛡️ FORÇAR REVISÃO EM CASOS CRÍTICOS (Chegada/Navegação)
    critical_keywords = ["cheguei", "chegada", "esteira", "mala", "aeroporto", "transporte", "onde", "como chegar", "ônibus", "trem", "uber"]
    is_arrival_query = any(kw in last_user_message.lower() for kw in critical_keywords)
    
    needs_review = not (hasattr(response, "tool_calls") and response.tool_calls) or is_arrival_query
    
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
                
                # Se for consulta de chegada/navegação, usar prompt especializado
                critical_keywords = ["cheguei", "chegada", "esteira", "mala", "aeroporto", "transporte", "onde", "como chegar", "ônibus", "trem", "uber"]
                if any(kw in user_query.lower() for kw in critical_keywords):
                    gemini_res = gemini_svc.verify_navigation_and_arrival(last_ai_message, user_query)
                else:
                    gemini_res = gemini_svc.get_second_opinion(last_ai_message, user_query)
                    
                if gemini_res:
                    gemini_opinion = gemini_res
                    logger.info("✅ Opinião do Gemini obtida.")
            except Exception as e:
                logger.error(f"Erro no Gemini: {e}")

        # 2. Obter refinamento final do Claude (Veredito)
        if settings.ANTHROPIC_API_KEY:
            try:
                from app.services.claude_service import ClaudeService
                claude_svc = ClaudeService()
                refined_res = claude_svc.get_refined_answer(user_query, last_ai_message, gemini_opinion)
                if refined_res:
                    final_response = refined_res
                    logger.info("✅ Veredito final do Claude obtido.")
            except Exception as e:
                logger.error(f"Erro no Claude: {e}")
        elif gemini_opinion:
            final_response = f"{last_ai_message}\n\n---\n✨ **Revisão de Segurança (Consenso IAs):**\n{gemini_opinion}"

        if not final_response or final_response == last_ai_message:
            # Se não houve refinamento ou falhou, mantemos o original mas logamos/notificamos
            if settings.ANTHROPIC_API_KEY and not final_response:
                 logger.warning("⚠️ Claude falhou no refinamento. Notificando Admin...")
                 n8n = N8nService()
                 admin_num = getattr(settings, "ADMIN_WHATSAPP_NUMBER", "")
                 if admin_num:
                     n8n.enviar_resposta_usuario(
                         admin_num, 
                         f"🚨 *ALERTA TRAVEL AI*\nO Claude 3.5 falhou por falta de créditos ou erro de API. Verifique sua conta Anthropic."
                     )
            final_response = last_ai_message

        return {"messages": [AIMessage(content=final_response)], "needs_gemini_review": False}
        
    except Exception as e:
        logger.error(f"Erro no Expert Review: {e}")
        return {"messages": [], "needs_gemini_review": False}

def route_after_agent(state: AgentState) -> Literal["tools", "expert_review", "end"]:
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
    
    # Atualiza ALL_TOOLS para incluir a nova ferramenta para o ToolNode
    current_tools_for_node = list(ALL_TOOLS)
    tool_node = ToolNode(current_tools_for_node)
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
