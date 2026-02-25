"""
Teste de Integração - APIs Profissionais
"""

from app.services.duffel_service import DuffelService
from app.services.serpapi_service import SerpApiService
from app.services.finance_service import FinanceService
from app.services.connectivity_service import ConnectivityService
from loguru import logger

def test_pro_apis():
    print("\n--- Iniciando Testes de Integracao Pro ---")
    
    # 1. Teste Duffel (Voos)
    print("\n[VOOS] Testando Duffel...")
    duffel = DuffelService()
    flight_res = duffel.search_flights("GRU", "CDG", "2026-05-15")
    print(flight_res[:500] + "..." if len(flight_res) > 500 else flight_res)
    
    # 2. Teste SerpApi (Hoteis)
    print("\n[HOTEIS] Testando SerpApi...")
    serp = SerpApiService()
    hotel_res = serp.search_hotels("Paris", "2026-05-15", "2026-05-20")
    print(hotel_res[:500] + "..." if len(hotel_res) > 500 else hotel_res)
    
    # 3. Teste Finance (Moeda)
    print("\n[FINANCE] Testando Finance...")
    finance = FinanceService()
    conv_res = finance.convert_currency(100, "USD", "BRL")
    print(conv_res)
    
    # 4. Teste Connectivity (eSIM)
    print("\n[INTERNET] Testando Connectivity...")
    conn = ConnectivityService()
    conn_res = conn.get_e_sim_recommendations("Franca")
    print(conn_res[:500] + "..." if len(conn_res) > 500 else conn_res)

if __name__ == "__main__":
    try:
        test_pro_apis()
        print("\nSUCCESS: Todos os servicos integrados!")
    except Exception as e:
        print(f"\nERROR durante os testes: {e}")
