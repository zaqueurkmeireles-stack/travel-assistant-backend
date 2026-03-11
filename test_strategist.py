from app.agents.orchestrator import TravelAgent
import sys
import io

# Forçar UTF-8 para evitar erros com emojis no terminal Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test_strategist_persona():
    print("--- TESTANDO MASTER ESTRATEGISTA (CRIAÇÃO DE ROTEIROS) ---")
    agent = TravelAgent()
    
    # Pergunta vaga inicial (A IA deve fazer perguntas da Fase 1 do prompt)
    pergunta1 = "Quero fazer uma viagem pra Europa."
    print(f"\nUsuário: {pergunta1}")
    resp1 = agent.chat(pergunta1, thread_id="test_strategist")
    print(f"IA (Fase 1 - Coleta): \n{resp1}\n")
    
    # Resposta detalhada (A IA deve gerar a estrutura de Roteiro de Ouro)
    pergunta2 = "Vamos para Paris em Outubro. Somos um casal, queremos algo focado em gastronomia e romance, orçamento moderado. Temos 3 dias."
    print(f"\nUsuário: {pergunta2}")
    resp2 = agent.chat(pergunta2, thread_id="test_strategist")
    print(f"IA (Fase 3 - Roteiro de Ouro): \n{resp2}\n")
    
    # Validação básica da estrutura
    if "Análise Estratégica" in resp2 or "Análise" in resp2 or "Roteiro de Ouro" in resp2 or "Custo-Benefício" in resp2:
        print("\n✅ OK: A IA adotou a persona e o formato do Estrategista!")
    else:
        print("\n❌ FALHA: A IA não utilizou a formatação obrigatória exigida no mega-prompt.")

if __name__ == "__main__":
    test_strategist_persona()
