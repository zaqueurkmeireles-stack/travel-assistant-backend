"""
Teste do TravelAgent com LangGraph
"""

from app.agents.orchestrator import TravelAgent
from loguru import logger

def test_agent():
    """Testa o agente com diferentes perguntas"""
    
    print("=" * 70)
    print("🧪 TESTANDO TRAVELAGENT COM LANGGRAPH")
    print("=" * 70)
    print()
    
    # Inicializar agente
    agent = TravelAgent()
    
    # Teste 1: Pergunta simples (não precisa de tools)
    print("📝 TESTE 1: Pergunta simples")
    print("-" * 70)
    response = agent.chat("Olá! O que você pode fazer por mim?")
    print(f"🤖 Resposta: {response}")
    print()
    
    # Teste 2: Clima (deve usar tool get_current_weather)
    print("📝 TESTE 2: Clima (deve chamar tool)")
    print("-" * 70)
    response = agent.chat("Qual é o clima em Paris agora?")
    print(f"🤖 Resposta: {response}")
    print()
    
    # Teste 3: Recomendações (deve usar tool get_travel_recommendations)
    print("📝 TESTE 3: Recomendações (deve chamar tool)")
    print("-" * 70)
    response = agent.chat("Me dê dicas para viajar para Tóquio. Gosto de tecnologia e gastronomia.")
    print(f"🤖 Resposta: {response}")
    print()
    
    print("=" * 70)
    print("✅ TESTES CONCLUÍDOS!")
    print("=" * 70)

if __name__ == "__main__":
    test_agent()