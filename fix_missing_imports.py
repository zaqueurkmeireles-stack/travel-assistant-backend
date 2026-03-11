file_path = "app/agents/orchestrator.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Definimos o bloco de imports completo e correto
header_imports = """from typing import TypedDict, Annotated, Literal
import sqlite3
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.checkpoint.sqlite import SqliteSaver

# 🛡️ Importação resiliente do add_messages
try:
    from langgraph.graph import add_messages
except ImportError:
    from langgraph.graph.message import add_messages
"""

# 2. Inserimos o header no topo do arquivo, removendo imports duplicados de BaseMessage ou TypedDict
# Vamos substituir as primeiras linhas de import pelo nosso bloco consolidado
lines = content.splitlines()
cleaned_lines = []
skip_old_imports = True

for line in lines:
    if skip_old_imports:
        # Pula os imports antigos até encontrar o início do código real
        if "class AgentState" in line or "conn = sqlite3.connect" in line or "# =" in line:
            skip_old_imports = False
            cleaned_lines.append(header_imports)
            cleaned_lines.append(line)
        continue
    cleaned_lines.append(line)

with open(file_path, "w", encoding="utf-8") as f:
    f.write("\n".join(cleaned_lines))

print("✅ Imports restaurados! O Antigravity agora reconhece 'add_messages' e 'BaseMessage'.")
