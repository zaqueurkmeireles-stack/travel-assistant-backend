import os
import sys
from datetime import datetime, timedelta

# Mock do n8n para nao enviar mensagem real
class MockN8n:
    def enviar_resposta_usuario(self, user_id, msg):
        print(f"\n--- MENSAGEM N8N PARA {user_id} ---\n{msg}\n-----------------------------------\n")

def simulate_deep_dive():
    print("TEST: SIMULANDO DEEP-DIVE DE ROTEIRO (D-10)")
    from app.services.scheduler_service import SchedulerService
    from app.services.trip_service import TripService
    
    # Configurar environment para omitir logs com emojis se possivel (ou apenas ignorar)
    
    sched = SchedulerService()
    sched.n8n_svc = MockN8n()
    
    # Criar uma viagem fake para teste D-10
    start_date = (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d")
    test_trip = {
        "id": "TEST_DEEP_DIVE_001",
        "user_id": "zaqueu_test",
        "primary_contact_id": "zaqueu_test",
        "destination": "Alemanha",
        "start_date": start_date,
        "points_of_interest": ["Mina de Sal de Berchtesgaden", "Ninho da Águia"],
        "alerts_sent": []
    }
    
    sched.trip_svc.trips = [test_trip]
    print(f"Viagem teste criada: {test_trip['destination']} em {test_trip['start_date']}")
    
    # Rodar o deep dive
    sched.itinerary_poi_deep_dive()

if __name__ == "__main__":
    # Remove emojis do encoding de output
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    # Adiciona o path atual para importar app
    sys.path.append(os.getcwd())
    simulate_deep_dive()
