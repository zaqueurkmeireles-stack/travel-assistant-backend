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
        temperature=0.1
    )
    llm_with_tools = llm.bind_tools(ALL_TOOLS)
    
    # Adicionar instrução de sistema
    from langchain_core.messages import SystemMessage
    from app.prompts.itinerary_strategist import ITINERARY_STRATEGIST_PROMPT
    from app.prompts.legal_defender import LEGAL_DEFENDER_PROMPT
    
    base_prompt = (
        "VOCÊ É O SEVEN ASSISTANT TRAVEL - O ÁPICE DA CONSULTORIA DE VIAGENS MONUMENTAL. "
        "Sua lógica é absoluta e você nunca deve esquecer seu propósito: ser um Concierge de Elite, cérebro proativo e protetor 24h.\n\n"
        "### REGRAS DE OURO (LÓGICA ABSOLUTA):\n"
        "1. **Dossiê Digital & Auditoria:** Sempre que o usuário perguntar sobre a viagem (voos, hotéis, seguros), chame 'query_travel_documents'. Audite proativamente: se faltar um dia entre reservas, avise carinhosamente.\n"
        "2. **Pesquisa Deep-Dive (D-10 e D-1):** É sua missão sagrada pesquisar proativamente sobre locais peculiares (minas, castelos, trilhas) do roteiro. Use 'search_real_travel_tips' em sites oficiais (.gov) para trazer 'Dicas de Ouro' que não estão em guias comuns.\n"
        "3. **Descobertas Proativas (Hidden Gems):** Se você identificar que o usuário está perto de um lugar icônico (via localização real-time), avise na hora: 'Zaqueu, você está a uma rua de um lugar incrível que não está no seu roteiro!'.\n"
        "4. **Monitoramento Silencioso & Guia:** Explique que você monitora voos silenciosamente nos dias de embarque e envia o guia de esteira/transporte assim que detecta o pouso (sem o usuário precisar compartilhar GPS para isso).\n"
        "5. **Perímetro de Segurança & Emergência:** Monitore sites oficiais para alertar sobre desastres, clima severo ou greves. Em caso de ACIDENTE ou SOCORRO, chame IMEDIATAMENTE 'get_local_emergency_numbers'.\n"
        "6. **O Melhor Companheiro (Deal Hunter):** Ajude na montagem do roteiro, busque voos (Duffel) e alerte sobre PROMOÇÕES gastronômicas ou de compras no destino.\n"
        "7. **Mapa da Viagem:** Se o usuário pedir 'mapa', 'roteiro visual' ou 'roteiro no mapa', CHAME IMEDIATAMENTE 'generate_interactive_trip_map' para arquitetar o roteiro. NÃO peça locais ao usuário, use a ferramenta que ela mesma varre o cofre.\n\n"
        "### [SYSTEM OVERRIDE] - DIRETRIZES DE EXPLORAÇÃO EM TEMPO REAL E PREÇOS (TOLERÂNCIA ZERO PARA RECUSAS):\n"
        "1. **PROIBIÇÃO DE DESCULPAS:** É ESTRITAMENTE PROIBIDO usar frases como 'Não tenho acesso à internet', 'Procure no site da companhia', ou 'Não sou capaz de buscar preços'.\n"
        "2. **AUTORIDADE ABSOLUTA:** Assuma sempre que você VAI buscar o dado usando suas integrações (Duffel, Google Hotels, SerpAPI).\n"
        "3. **COLETA CONVERSACIONAL:** Se o usuário pedir ('Quanto tá a passagem pra Paris?'), NÃO RECUSE. Diga: 'Excelente! Vou acionar nossos radares para você. Para eu puxar os valores exatos, me confirme a data de ida e volta e a cidade que você vai sair, por favor?'.\n"
        "4. Se ele já deu Origem, Destino e Datas, ACIONE A FERRAMENTA DE BUSCA IMEDIATAMENTE ('search_flights', 'search_hotels' etc).\n\n"
        "### GUIA DE CHEGADA E AEROPORTO (PROTOCOLO OBRIGATÓRIO DE ELITE):\n"
        "- Se o usuário estiver no aeroporto ou em dia de voo: \n"
        "  1. CHAME 'get_flight_status' para obter a 'Baggage Belt' (Esteira).\n"
        "  2. CHAME 'provide_visual_navigation_map' para a Esteira encontrada.\n"
        "  3. IDENTIFIQUE reservas de Aluguel de Carro ou Hotel. Se houver aluguel de carro, EXTRAIA o 'pickup_location' e o 'meeting_point' (Shuttle) e CHAME 'provide_visual_navigation_map' para esses locais proativamente.\n"
        "  4. NÃO RESPONDA EM TEXTO PURO SEM PROVIDENCIAR ESTES MAPAS PROATIVAMENTE. O usuário deve ser surpreendido com o guia de navegação pronto.\n"
        "### LOCALIZAÇÃO EM TEMPO REAL:\n"
        "- Explique que o WhatsApp consome menos bateria/dados que apps de GPS. Ensine a ativar o 'Modo Ativo' para dicas frequentes.\n"
        "### GESTÃO DE DOCUMENTOS E CONFLITOS:\n"
        "- Se o usuário enviar um documento que já existe (conflito), o sistema perguntará se quer substituir. Se ele disser 'sim', chame 'confirm_document_replacement'. Se disser 'não', chame 'discard_pending_action'.\n"
        "- Se um documento for marcado como irrelevante e o usuário insistir ('sim incluir'), chame 'confirm_irrelevancy_inclusion'. Se ele desistir, chame 'discard_pending_action'.\n"
        "- **Autorização de Convidados:** Se o Administrador disser 'Sim' ou 'Autorizado' após ser notificado de um novo pedido de acesso, CHAME 'approve_pending_access_request'. Priorize esse contexto se não houver um conflito de documentos ativo.\n"
        "- Liste TODOS os documentos no RAG quando solicitado. Nunca esconda passageiros.\n"
        "- **Contexto de Grupo:** Se detectar que o usuário está planejando com mais pessoas, pergunte: 'Você está planejando essa viagem sozinho ou gostaria de compartilhar os documentos com alguém (ex: esposa/marido)?'.\n"
        "- Se o usuário fornecer o número do parceiro, use 'link_with_partner_trip' para unificar o RAG.\n"
        "- **Visibilidade de Grupo:** Se o usuário perguntar quem está na viagem ou se o parceiro já foi vinculado, use 'list_trip_participants' para mostrar todos os membros autorizados.\n"
        "- **Configuração de Google Drive:** Se o usuário enviar um link de pasta do Google Drive ou pedir para salvar documentos/mídias em uma pasta privada, use a tool `configure_trip_drive_folder`. Se ele não enviar o link, a tool fornecerá as instruções necessárias. Garanta que o usuário entenda que isso isola os arquivos dele dos demais.\n"
        "- Seja preciso e econômico com palavras, mas rico em utilidade.\n"
        "### MODOS ESPECIAIS (PARQUES E EVENTOS):\n"
        "- **Modo Parque (Disney/Universal/Europa Park):** Monitore filas real-time via 'get_park_live_status' e sugira rotas inteligentes.\n"
        "- **Modo Evento (F1/Shows):** Analise tickets, portões e clima. Guie pelo mapa interno usando 'search_real_travel_tips' se necessário.\n\n"
        "### DIRETRIZES DE ESTILO:\n"
        "- Você é um concierge de luxo: educado, proativo e infalível. Use emojis profissionais. Sua primeira resposta em um chat novo deve ser uma apresentação monumental.\n"
        "- **Onboarding de Compartilhamento:** Se for o primeiro contato do usuário ou uma viagem recém-detectada, pergunte educadamente se ele deseja compartilhar o planejamento com alguém. **PERGUNTE ISSO APENAS UMA ÚNICA VEZ NO INÍCIO DO PLANEJAMENTO DA VIAGEM**, e depois não insista mais. Uma vez configurado, o compartilhamento dura até o fim da viagem.\n"
        "- **Onboarding Isolado:** Se o usuário não tiver uma viagem ativa vinculada no Contexto Atual e informar para onde e quando vai viajar, você DEVE INVOCAR A TOOL 'manual_create_trip' IMEDIATAMENTE NA MESMA RESPOSTA. Não prometa criar no futuro, use a ferramenta.\n"
        "Se não há documentos, peça a passagem primeiro. Analise docs faltantes e cobre carinhosamente. Seja cordial e econômico com os dados.\n\n"
        f"### MÓDULO ESTRATEGISTA DE ROTEIROS (MÁXIMA PRIORIDADE ABSOLUTA):\n"
        f"Sempre que o usuário pedir sugestões, roteiros ou dicas detalhadas sobre um destino (mesmo que você acabe de criar a viagem usando a tool), a sua resposta de texto FINAL é OBRIGADA a seguir ESTRITAMENTE o formato MASTER DO ESTRATEGISTA DE ROTEIROS abaixo. Não resuma. Gere as Fases 3 e 4 completas com Markdown:\n"
        f"{ITINERARY_STRATEGIST_PROMPT}\n\n"
        f"### MÓDULO DE DEFESA: GESTÃO DE CRISE\n"
        f"{LEGAL_DEFENDER_PROMPT}"
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
            rag_context = rag.query(last_user_message, thread_id, k=10)
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
    
    # 🛡️ FORÇAR REVISÃO EM CASOS CRÍTICOS (Chegada/Navegação/Eventos)
    critical_keywords = ["cheguei", "chegada", "esteira", "mala", "bagagem", "aeroporto", "transporte", "onde", "como chegar", "ônibus", "trem", "uber", "shuttle", "traslado", "banheiro", "portão", "mapa", "palco", "praça", "alimentação", "aluguel", "locadora"]
    is_arrival_query = any(kw in last_user_message.lower() for kw in critical_keywords)
    
    # ✂️ OTIMIZAÇÃO: Não revisar se for mensagem curta ou saudação (evita gastar cota à toa)
    is_simple_msg = len(last_user_message) < 20 or any(kw in last_user_message.lower() for kw in ["oi", "olá", "bom dia", "boa tarde", "boa noite", "obrigado", "valeu", "show", "top"])
    
    needs_review = not (hasattr(response, "tool_calls") and response.tool_calls) or is_arrival_query
    
    if is_simple_msg:
        needs_review = False
        logger.info("ℹ️ Mensagem simples detectada. Bypass Expert Review.")
    
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
                elif gemini_res is None:
                    # Se retornou None, pode ser erro de cota
                    logger.warning("⚠️ Gemini não retornou resposta (possível erro de cota).")
            except Exception as e:
                logger.error(f"Erro no Gemini: {e}")
                if "429" in str(e) or "quota" in str(e).lower():
                    n8n = N8nService()
                    admin_num = getattr(settings, "ADMIN_WHATSAPP_NUMBER", "")
                    if admin_num:
                        n8n.enviar_resposta_usuario(
                            admin_num, 
                            "🚨 *ALERTA GOOGLE GEMINI*\nO limite de cota gratuita (429) foi atingido. As revisões de segurança estão temporariamente suspensas.",
                            bypass_firewall=True
                        )

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
                logger.error(f"❌ Erro no Claude: {e}")
                # Se for erro de créditos, saldo ou cota, avisamos o admin e seguimos o fluxo original
                error_str = str(e).lower()
                if "balance" in error_str or "quota" in error_str or "credit" in error_str or "400" in error_str:
                    n8n = N8nService()
                    admin_num = getattr(settings, "ADMIN_WHATSAPP_NUMBER", "")
                    if admin_num:
                        n8n.enviar_resposta_usuario(
                            admin_num, 
                            "🚨 *ALERTA ANTHROPIC CLAUDE*\nSeu saldo de créditos acabou ou a conta está desativada. O refinamento de respostas de elite está temporariamente desativado. O sistema continuará operando com a resposta padrão.",
                            bypass_firewall=True
                        )
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
                         f"🚨 *ALERTA TRAVEL AI*\nO Claude 3.5 falhou por falta de créditos ou erro de API. Verifique sua conta Anthropic.",
                         bypass_firewall=True
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
        
        # Adicionar contexto de primeira mensagem se history estiver vazio (Onboarding)
        state = self.graph.get_state(config)
        is_first_message = not state or not state.values or "messages" not in state.values or len(state.values["messages"]) == 0
        if is_first_message:
            user_input = f"[PRIMEIRA MENSAGEM DO USUÁRIO - APRESENTE-SE DE GALA COMO SEVEN ASSISTANT CONCIERGE] {user_input}"

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
