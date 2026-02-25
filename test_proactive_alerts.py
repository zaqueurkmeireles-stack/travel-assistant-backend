"""
Teste de Alertas Proativos - Simulação de datas para disparar notificações.
"""

from datetime import datetime, timedelta
from app.services.trip_service import TripService
from app.services.scheduler_service import SchedulerService
import json
import os

def test_proactive_alerts():
    print("[*] Iniciando teste de Alertas Proativos...")
    
    trip_svc = TripService()
    # Limpar base de testes se necessário ou usar um ID único
    user_id = "test_user_alerts_999"
    
    # Simular diferentes cenários de viagem
    today = datetime.now()
    
    scenarios = [
        {"destination": "D7-Place", "start_date": (today + timedelta(days=7)).strftime("%Y-%m-%d"), "label": "D-7 (Aviso 1 semana)"},
        {"destination": "D1-Place", "start_date": (today + timedelta(days=1)).strftime("%Y-%m-%d"), "label": "D-1 (Aviso amanha)"},
        {"destination": "D0-Place", "start_date": today.strftime("%Y-%m-%d"), "label": "D-0 (Dia da Viagem)"},
    ]
    
    for scene in scenarios:
        print(f"[*] Criando viajem para teste: {scene['label']} -> {scene['destination']} em {scene['start_date']}")
        trip_svc.add_trip_from_doc(user_id, scene)

    # 2. Simular execução do Scheduler
    print("\n[*] Acionando verificação de alertas do Scheduler...")
    scheduler = SchedulerService()
    
    # Injetamos o n8n_svc simulado para não enviar de verdade (opcional, mas o n8n_svc atual já simula se não houver URL)
    scheduler.check_and_send_alerts()
    
    print("\n[*] Verificando se alertas foram enviados (alerts_sent no JSON)...")
    # Recarregar trips
    trip_svc._load_trips()
    
    success_count = 0
    for trip in trip_svc.trips:
        if trip["user_id"] == user_id:
            if trip["alerts_sent"]:
                print(f"[SUCCESS] Alerta enviado para {trip['destination']}: {trip['alerts_sent']}")
                success_count += 1
            else:
                print(f"[FAILURE] Alerta NÃO enviado para {trip['destination']}")

    if success_count == 3:
        print("\n[SUCCESS] Todos os alertas proativos funcionaram!")
    else:
        print(f"\n[PARTIAL] {success_count}/3 alertas enviados.")

if __name__ == "__main__":
    test_proactive_alerts()
