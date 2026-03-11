file_path = "app/agents/orchestrator.py"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Troca o import e a inicialização da memória
content = content.replace(
    "from langgraph.checkpoint.memory import MemorySaver",
    "from langgraph.checkpoint.sqlite import SqliteSaver\nimport sqlite3"
)

# Substitui a lógica de criação da memória para usar o arquivo local
old_mem = "memory = MemorySaver()"
new_mem = """conn = sqlite3.connect("checkpoints.sqlite", check_same_thread=False)
        memory = SqliteSaver(conn)"""

if old_mem in content:
    content = content.replace(old_mem, new_mem)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("✅ Memória Evoluída! O Antigravity agora salva conversas em 'checkpoints.sqlite'.")
else:
    print("⚠️ Não foi possível encontrar a linha de inicialização da memória.")
