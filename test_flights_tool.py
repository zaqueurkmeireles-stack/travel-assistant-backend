from app.agents.orchestrator import TravelAgent
import json

def test_flights_tool():
    agent = TravelAgent()
    # Usando um voo comum para teste ou apenas perguntando de forma genérica
    user_input = "Qual o status do voo LA3110 hoje?"
    print(f"[*] Testando ferramenta de voos (AeroDataBox) com: '{user_input}'")
    
    try:
        response = agent.chat(user_input, thread_id="test_user_flights")
        print(f"\n[AGENT RESPONSE]\n{response}\n")
    except Exception as e:
        print(f"[ERROR] Erro ao testar voos: {e}")

if __name__ == "__main__":
    test_flights_tool()
