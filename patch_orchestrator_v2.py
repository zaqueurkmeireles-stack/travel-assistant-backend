file_path = "app/agents/orchestrator.py"

with open(file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
skip = False

# Adiciona o import necessário no topo se não existir
has_import = any("from app.agents.specialized import get_llm" in line for line in lines)
if not has_import:
    new_lines.append("from app.agents.specialized import get_llm\n")

for line in lines:
    # Quando encontrar o início da função antiga, começa a pular as linhas dela
    if "def call_model(state: AgentState, config: dict = None):" in line:
        skip = True
        new_lines.append(line) # Mantém a assinatura da função
        new_lines.append("    \"\"\"Nó principal: Chama o motor de IA resiliente com acesso às ferramentas\"\"\"\n")
        new_lines.append("    from loguru import logger\n")
        new_lines.append("    logger.info(\"🤖 Acionando Agente Antigravity (Motor Resiliente)...\")\n")
        new_lines.append("    \n")
        new_lines.append("    messages = state[\"messages\"]\n")
        new_lines.append("    \n")
        new_lines.append("    # Busca o motor de IA (OpenAI ou Gemini de backup)\n")
        new_lines.append("    model = get_llm()\n")
        new_lines.append("    \n")
        new_lines.append("    # Liga o cérebro às ferramentas (Duffel, Maps, Clima, etc)\n")
        new_lines.append("    model_with_tools = model.bind_tools(ALL_TOOLS)\n")
        new_lines.append("    \n")
        new_lines.append("    # Executa a chamada\n")
        new_lines.append("    response = model_with_tools.invoke(messages)\n")
        new_lines.append("    \n")
        new_lines.append("    return {\"messages\": [response]}\n\n")
        continue
    
    # Para de pular quando encontrar o próximo marcador de seção (geralmente comentários com ==)
    if skip and ("# =" in line or "class" in line or "def " in line):
        skip = False
    
    if not skip:
        new_lines.append(line)

with open(file_path, "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print("✅ Fusão completa sem erros de Regex! O Antigravity está blindado.")
