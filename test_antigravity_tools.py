import asyncio
from dotenv import load_dotenv
from app.agents.orchestrator import TravelAgent
from loguru import logger
import sys

# Carrega as chaves
load_dotenv()

async def test_cyborg_action():
    print("\n" + "="*60)
    print("🤖 TESTE DE AÇÃO ANTIGRAVITY: CHAMADA DE FERRAMENTA")
    print("="*60 + "\n")
    
    try:
        # Inicializa o Agente (que agora usa o nosso motor resiliente)
        agent = TravelAgent()
        
        # Pergunta que FORÇA o uso de uma ferramenta (Duffel/AeroDataBox)
        pergunta = "Pode verificar para mim o status do voo AD1234 para hoje?"
        
        print(f"👤 Usuário: {pergunta}")
        print("⏳ O Agente está processando e escolhendo a melhor ferramenta...\n")
        
        # O método chat do seu TravelAgent executa o LangGraph
        # Usamos thread_id para manter a "memória" da conversa
        resposta = agent.chat(pergunta, thread_id="teste_vips_001")
        
        print("\n" + "="*60)
        print("🌟 RESPOSTA DO AGENTE")
        print("="*60)
        print(f"\n{resposta}\n")
        
    except Exception as e:
        print(f"\n❌ ERRO NO TESTE: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Ajuste para evitar erros de loop no Windows
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(test_cyborg_action())
