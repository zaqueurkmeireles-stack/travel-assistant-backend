import re

file_path = "app/agents/orchestrator.py"
with open(file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
skip_until_end_of_block = False

# 1. Colocamos os imports essenciais logo no topo para evitar confusão
new_lines.append("from typing import TypedDict, Annotated, Literal\n")
new_lines.append("import sqlite3\n")
new_lines.append("from langgraph.checkpoint.sqlite import SqliteSaver\n")

# Filtramos os imports antigos que podem estar duplicados ou quebrados
for line in lines:
    if "from langgraph.checkpoint" in line or "import sqlite3" in line:
        continue
    
    # 2. Quando chegamos na parte da "Defesa" da memória, limpamos o bloco antigo
    if "# 🛡️ DEFESA" in line or "try:" in line and "MemorySaver" in lines[lines.index(line)+1 if lines.index(line)+1 < len(lines) else 0]:
        skip_until_end_of_block = True
        new_lines.append("\n# ============================================================\n")
        new_lines.append("# PERSISTÊNCIA DE MEMÓRIA (Antigravity Core)\n")
        new_lines.append("# ============================================================\n")
        new_lines.append("conn = sqlite3.connect('checkpoints.sqlite', check_same_thread=False)\n")
        new_lines.append("memory = SqliteSaver(conn)\n")
        continue

    # Para de pular quando o bloco de setup da memória acabar (geralmente antes do AgentState)
    if skip_until_end_of_block and "class AgentState" in line:
        skip_until_end_of_block = False
    
    if not skip_until_end_of_block:
        new_lines.append(line)

# 3. Garantimos que o workflow.compile use o checkpointer correto
content = "".join(new_lines)
content = re.sub(r'app = workflow\.compile\(.*?\)', 'app = workflow.compile(checkpointer=memory)', content)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("✅ Orquestrador Antigravity reparado e limpo!")
