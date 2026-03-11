"""
Script para testar a funcionalidade de parques (ParkService).
"""
import sys
import os
from loguru import logger

# Adicionar o diretório raiz ao path para permitir imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from app.services.park_service import ParkService

def test_parks():
    print("🎢 [TESTE] Validando ParkService...")
    service = ParkService()
    
    park_name = "magic_kingdom"
    print(f"[*] Buscando dados reais para: {park_name}")
    
    live_data = service.get_live_data(park_name)
    if live_data:
        print(f"✅ Recebidos {len(live_data)} itens de dados em tempo real.")
        
        # Testar formatação
        summary = service.format_park_summary(live_data)
        print("\n=== RESUMO FORMATADO ===")
        print(summary)
        print("========================\n")
    else:
        print("❌ Falha ao obter dados em tempo real ou parque está fechado.")

if __name__ == "__main__":
    try:
        test_parks()
    except Exception as e:
        print(f"💥 Erro durante o teste: {e}")
