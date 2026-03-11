import asyncio
from dotenv import load_dotenv
import time

# Carrega as chaves de API
load_dotenv()

from app.services.ai_orchestrator import AIOrchestrator

async def run_trial_by_fire():
    print("\n" + "="*50)
    print("🚀 INICIANDO TESTE DE FOGO: A TRÍADE DE IAs")
    print("="*50 + "\n")
    
    try:
        orchestrator = AIOrchestrator()
        
        pergunta = "Quero fazer uma viagem rápida de fim de semana para a capital do Paraná. O que você me recomenda fazer em 2 dias?"
        print(f"👤 Cliente: '{pergunta}'\n")
        
        start_time = time.time()
        
        # Chama o Orquestrador diretamente
        resposta_final = await orchestrator.process_message(pergunta)
        
        elapsed = time.time() - start_time
        
        print("\n" + "="*50)
        print(f"🌟 VEREDITO FINAL (Tempo: {elapsed:.2f}s)")
        print("="*50)
        print(f"\n{resposta_final}\n")
        
    except Exception as e:
        print(f"\n❌ ERRO NO TESTE: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_trial_by_fire())
