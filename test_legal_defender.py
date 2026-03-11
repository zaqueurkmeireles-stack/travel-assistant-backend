from app.agents.orchestrator import TravelAgent
import sys
import io

# Forçar UTF-8 no stdout
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test_legal_defender():
    print("--- TESTANDO MASTER DEFENDER (GESTÃO DE CRISE) ---")
    agent = TravelAgent()
    
    # Teste 1: Europa (EU261)
    pergunta1 = "Meu voo da Air France saindo de Paris para Roma acabou de ser cancelado. Estou desesperado no aeroporto, o que eu faço? E meus direitos?"
    print(f"\nUsuário (EU261): {pergunta1}")
    resp1 = agent.chat(pergunta1, thread_id="test_defender")
    print(f"\nIA (Defensor Europa): \n{resp1}\n")
    print("-" * 50)
    
    # Teste 2: Brasil (ANAC)
    pergunta2 = "Estava indo de São Paulo pra Salvador pela LATAM e atrasou 5 horas do nada. Eles não querem pagar hotel. Isso dá processo por danos morais? Quero processar!"
    print(f"\nUsuário (ANAC): {pergunta2}")
    resp2 = agent.chat(pergunta2, thread_id="test_defender")
    print(f"\nIA (Defensor Brasil): \n{resp2}\n")
    print("-" * 50)

    # Verifica se os checklists e territorialidades estão sendo acionados
    if "Checklist" in resp1 or "Checklist" in resp2 or ("261" in resp1 and "ANAC" in resp2):
        print("\n✅ OK: O Defensor de Crise assumiu as regras territoriais corretamente.")
    else:
        print("\n❌ AVISO: A resposta pode não estar seguindo o mega-prompt estritamente.")

if __name__ == "__main__":
    test_legal_defender()
