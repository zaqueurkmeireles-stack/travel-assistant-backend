from app.services.booking_service import BookingService
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test_booking_service():
    print("--- TESTE BOOKING SERVICE ---")
    service = BookingService()
    
    city = "Curitiba"
    checkin = "2026-10-10"
    checkout = "2026-10-15"
    
    print(f"\nBuscando Dest ID para {city}...")
    dest_id = service._get_dest_id(city)
    print(f"Dest ID encontrado: {dest_id}")
    
    print(f"\nBuscando hotéis em {city} de {checkin} a {checkout}...")
    result = service.search_hotels(city, checkin, checkout)
    print("\nResultado da Busca:")
    print(result)

if __name__ == "__main__":
    test_booking_service()
