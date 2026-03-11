from app.agents.orchestrator import TravelAgent
import sys
import io

# Forçar UTF-8 para evitar erros com emojis no terminal Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test_flight_search_behavior():
    print("--- TESTANDO COMPORTAMENTO DE BUSCA DE VOOS (SYSTEM OVERRIDE) ---")
    agent = TravelAgent()
    
    # Pergunta vaga sem dados suficientes
    pergunta1 = "Quanto tá a passagem para Paris em julho?"
    print(f"\nUsuário: {pergunta1}")
    resp1 = agent.chat(pergunta1, thread_id="test_override")
    print(f"IA: {resp1}")
    
    if "não tenho" in resp1.lower() or "não posso" in resp1.lower():
        print("\n❌ FALHA: A IA deu uma resposta de recusa padrão!")
    else:
        print("\n✅ OK: A IA respondeu de forma colaborativa solicitando dados!")

if __name__ == "__main__":
    test_flight_search_behavior()
