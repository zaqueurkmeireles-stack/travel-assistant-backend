import sys
from app.agents.orchestrator import TravelAgent
from app.parsers.car_rental_parser import CarRentalParser

def quick_verify():
    print("--- INICIANDO VERIFICACAO RAPIDA ---")
    
    # 1. Testar Parser de Carro com novo Prompt
    print("1. Testando CarRentalParser...")
    parser = CarRentalParser()
    test_text = "Rental Voucher: Hertz. Pickup: JFK Terminal 4. Shuttle at Door 2. Date: 2026-05-10."
    res = parser.parse(test_text.encode('utf-8'), "test_hertz.txt")
    if res.get("document_type") == "car_rental":
        print("   OK: Parser reconheceu o tipo corretamente.")
    else:
        print("   ERRO: Falha no Parser.")

    # 2. Testar Orquestrador (Proatividade)
    print("2. Testando Orquestrador (Chat)...")
    agent = TravelAgent()
    user_msg = "Cheguei no aeroporto. Onde pego meu carro alugado?"
    response = agent.chat(user_msg, thread_id="test_verify_123")
    print(f"   Resposta IA: {response[:100]}...")
    
    if "MAPA" in response.upper() or "ESTEIRA" in response.upper() or "RESERVA" in response.upper():
        print("   OK: Resposta proativa detectada.")
    else:
        print("   AVISO: Verifique se a proatividade foi acionada corretamente no orquestrador.")

    print("--- VERIFICACAO CONCLUIDA ---")

if __name__ == "__main__":
    quick_verify()
