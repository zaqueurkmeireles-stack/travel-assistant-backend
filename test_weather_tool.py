import asyncio
from app.agents.orchestrator import TravelAgent
from loguru import logger
import json

def test_weather_tool():
    agent = TravelAgent()
    
    # Pergunta que deve acionar a ferramenta de clima
    user_input = "Como está o tempo em Curitiba?"
    print(f"[*] Testando ferramenta de clima com: '{user_input}'")
    
    try:
        response = agent.chat(user_input, thread_id="test_user_weather")
        print(f"\n[AGENT RESPONSE]\n{response}\n")
    except Exception as e:
        print(f"[ERROR] Erro ao testar ferramenta de clima: {e}")

if __name__ == "__main__":
    test_weather_tool()
