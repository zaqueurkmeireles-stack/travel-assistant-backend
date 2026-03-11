import os

file_path = "app/agents/orchestrator.py"

content = """from typing import TypedDict, Annotated, Literal
import sqlite3
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from loguru import logger
from app.agents.tools import ALL_TOOLS
from app.agents.specialized import get_llm

# 🛡️ Importação resiliente do add_messages
try:
    from langgraph.graph import add_messages
except ImportError:
    from langgraph.graph.message import add_messages

# ============================================================
# PERSISTÊNCIA DE MEMÓRIA (Antigravity Core)
# ============================================================
conn = sqlite3.connect('checkpoints.sqlite', check_same_thread=False)
memory = SqliteSaver(conn)

# ============================================================
# ESTADO DO AGENTE
# ============================================================
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    needs_gemini_review: bool

# ============================================================
# NÓS DO GRAFO
# ============================================================

def call_model(state: AgentState, config: dict = None):
    logger.info("🤖 Acionando Agente Antigravity (Motor Resiliente)...")
    messages = state["messages"]
    model = get_llm()
    model_with_tools = model.bind_tools(ALL_TOOLS)
    response = model_with_tools.invoke(messages)
    return {"messages": [response]}

def route_after_agent(state: AgentState):
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools"
    return "end"

# ============================================================
# CLASSE PRINCIPAL (O Piloto)
# ============================================================
class TravelAgent:
    def __init__(self):
        from langgraph.graph import StateGraph, END
        from langgraph.prebuilt import ToolNode
        
        workflow = StateGraph(AgentState)
        workflow.add_node("agent", call_model)
        workflow.add_node("tools", ToolNode(ALL_TOOLS))
        
        workflow.set_entry_point("agent")
        workflow.add_conditional_edges("agent", route_after_agent, {"tools": "tools", "end": END})
        workflow.add_edge("tools", "agent")
        
        self.app = workflow.compile(checkpointer=memory)
        logger.info("✅ Grafo Antigravity compilado com Persistência SQLite.")

    def chat(self, user_input: str, thread_id: str = "default_thread"):
        config = {"configurable": {"thread_id": thread_id}}
        input_message = HumanMessage(content=user_input)
        
        final_state = self.app.invoke({"messages": [input_message]}, config)
        return final_state["messages"][-1].content
"""

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("✅ CLASSE RESTAURADA! O TravelAgent está de volta ao comando.")
