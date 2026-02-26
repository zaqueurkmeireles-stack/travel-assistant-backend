"""
Teste do TravelAgent com LangGraph (Simulando fluxo do WhatsApp/n8n)
"""

from app.agents.orchestrator import TravelAgent
from loguru import logger

def test_agent():
    """Testa o agente simulando conversas reais com memória"""
    
    print("=" * 70)
    print("TESTANDO TRAVELAGENT COM LANGGRAPH E MEMORIA")
    print("=" * 70)
    print()
    
    # Inicializar agente
    agent = TravelAgent()
    
    # Simulando um número de WhatsApp vindo do n8n (usado como thread_id)
    numero_whatsapp = "5511999999999"
    
    # Teste 1: Apresentacao (A IA deve guardar isso na memoria)
    print("TESTE 1: Apresentacao (Guardando na memoria)")
    print("-" * 70)
    pergunta_1 = "Olá! Meu nome é Carlos e vou para Paris mês que vem."
    print(f"Usuário ({numero_whatsapp}): {pergunta_1}")
    
    response = agent.chat(user_input=pergunta_1, thread_id=numero_whatsapp)
    print(f"IA: {response}\n")
    
    # Teste 2: Contexto (A IA deve usar a tool de clima e lembrar que e Paris)
    print("TESTE 2: Clima (Testando uso de Ferramenta + Memoria)")
    print("-" * 70)
    pergunta_2 = "Como está o clima lá agora?" # "Lá" exige que a IA puxe "Paris" da memória
    print(f"Usuário ({numero_whatsapp}): {pergunta_2}")
    
    response = agent.chat(user_input=pergunta_2, thread_id=numero_whatsapp)
    print(f"IA: {response}\n")
    
    # Teste 3: Resgate de Memoria Explicita
    print("TESTE 3: Resgate de Memoria e Recomendacoes")
    print("-" * 70)
    pergunta_3 = "Você lembra o meu nome? Me dê 3 dicas de restaurantes bons por lá."
    print(f"Usuário ({numero_whatsapp}): {pergunta_3}")
    
    response = agent.chat(user_input=pergunta_3, thread_id=numero_whatsapp)
    print(f"IA: {response}\n")
    
    print("=" * 70)
    print("TESTES CONCLUIDOS COM SUCESSO!")
    print("=" * 70)

if __name__ == "__main__":
    test_agent()