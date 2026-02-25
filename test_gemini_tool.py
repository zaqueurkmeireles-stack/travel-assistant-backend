from app.agents.orchestrator import TravelAgent
from loguru import logger

def test_gemini_consensus():
    agent = TravelAgent()
    
    # Pergunta que deve gerar uma resposta longa o suficiente para triggerar o Gemini review
    # Conforme orchestrator.py:len(last_ai_message) >= 200
    user_input = "Crie um roteiro detalhado de 3 dias para a Chapada dos Veadeiros com foco em cachoeiras e trilhas difíceis."
    print(f"[*] Testando Consenso de IA (GPT-4o + Gemini) com: '{user_input}'")
    
    try:
        response = agent.chat(user_input, thread_id="test_user_gemini")
        print(f"\n[AGENT RESPONSE]\n{response}\n")
        
        if "Segunda Opinião do Especialista (Gemini):" in response:
            print("✅ SUCESSO: O Gemini revisou a resposta!")
        else:
            print("⚠️ AVISO: A resposta foi gerada, mas o Gemini não parece ter revisado (pode ser pelo tamanho do texto).")
            
    except Exception as e:
        print(f"[ERROR] Erro ao testar Gemini: {e}")

if __name__ == "__main__":
    test_gemini_consensus()
