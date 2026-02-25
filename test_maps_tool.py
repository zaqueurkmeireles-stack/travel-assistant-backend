from app.agents.orchestrator import TravelAgent
import json

def test_maps_tool():
    agent = TravelAgent()
    user_input = "Busque 3 bons restaurantes em Alto Paraíso de Goiás."
    print(f"[*] Testando ferramenta de mapas (Google Maps) com: '{user_input}'")
    
    try:
        response = agent.chat(user_input, thread_id="test_user_maps")
        print(f"\n[AGENT RESPONSE]\n{response}\n")
    except Exception as e:
        print(f"[ERROR] Erro ao testar mapas: {e}")

if __name__ == "__main__":
    test_maps_tool()
