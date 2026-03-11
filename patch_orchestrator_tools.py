import re

file_path = "app/agents/orchestrator.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Adicionar o import do get_llm
if "from app.agents.specialized import get_llm" not in content:
    content = content.replace(
        "from app.agents.tools import ALL_TOOLS",
        "from app.agents.tools import ALL_TOOLS\nfrom app.agents.specialized import get_llm"
    )

# 2. Atualizar a lógica do call_model para usar o motor resiliente com ferramentas
# Localizamos o início da função e injetamos a chamada bindada com as ferramentas
pattern = r'(def call_model\(state: AgentState, config: dict = None\):.*?\n)(.*?)(?=\n#)'
replacement = r'''\1    """Nó principal: Chama o motor de IA resiliente com acesso às ferramentas"""
    logger.info("🤖 Acionando Agente Antigravity (Motor Resiliente)...")
    
    messages = state["messages"]
    
    # Busca o motor de IA (OpenAI ou Gemini de backup)
    model = get_llm()
    
    # Liga o cérebro às ferramentas (Duffel, Maps, Clima, etc)
    model_with_tools = model.bind_tools(ALL_TOOLS)
    
    # Executa a chamada
    response = model_with_tools.invoke(messages)
    
    return {"messages": [response]}

'''

# Aplicando a substituição
if "model_with_tools =" not in content:
    content = re.sub(r'def call_model.*?return \{"messages": \[response\]\}', replacement, content, flags=re.DOTALL)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("✅ Fusão completa! O Antigravity agora usa IAs resilientes com todas as Tools.")
else:
    print("⚠️ A função call_model parece já estar atualizada ou em um formato diferente.")
