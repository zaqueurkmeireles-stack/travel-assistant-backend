"""
Teste de Geolocalização - Simula chegada ao destino da viagem.
"""

from app.services.geolocation_service import GeolocationService
from app.services.trip_service import TripService
from datetime import datetime
import json

def test_geolocation_arrival():
    print("[*] Iniciando teste de Geolocalização...")
    
    # 1. Configurar uma viagem para hoje
    user_id = "geo_test_user_777"
    destination = "Frankfurt"
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    trip_svc = TripService()
    trip_svc.add_trip_from_doc(user_id, {
        "destination": destination,
        "start_date": today_str
    })
    
    # 2. Simular coordenadas de Frankfurt (aprox 50.11, 8.68)
    lat_frankfurt = 50.1109
    lng_frankfurt = 8.6821
    
    print(f"[*] Simulando chegada em {destination} ({lat_frankfurt}, {lng_frankfurt})...")
    
    geo_svc = GeolocationService()
    message = geo_svc.process_location(user_id, lat_frankfurt, lng_frankfurt)
    
    if message and "Bem-vindo" in message:
        print("\n✅ SUCESSO: Guia de chegada gerado corretamente!")
        print("-" * 50)
        print(message)
        print("-" * 50)
    else:
        print("\n❌ FALHA: Guia de chegada NÃO foi gerado.")

    # 3. Testar se ele não envia duplicado
    print("\n[*] Testando se evita envio duplicado...")
    message_dup = geo_svc.process_location(user_id, lat_frankfurt, lng_frankfurt)
    if message_dup is None:
        print("✅ SUCESSO: Sistema evitou duplicidade de alerta.")
    else:
        print("❌ FALHA: Sistema enviou alerta duplicado.")

if __name__ == "__main__":
    test_geolocation_arrival()
