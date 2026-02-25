from app.agents.orchestrator import TravelAgent
import json

def test_tavily_tool():
    agent = TravelAgent()
    user_input = "Quais as melhores dicas reais de quem já foi para a Chapada dos Veadeiros no Reddit?"
    print(f"[*] Testando ferramenta de busca (Tavily) com: '{user_input}'")
    
    try:
        response = agent.chat(user_input, thread_id="test_user_tavily")
        print(f"\n[AGENT RESPONSE]\n{response}\n")
    except Exception as e:
        print(f"[ERROR] Erro ao testar Tavily: {e}")

if __name__ == "__main__":
    test_tavily_tool()
