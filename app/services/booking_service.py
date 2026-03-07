import requests
import json
from datetime import datetime
from loguru import logger
from app.config import settings

class BookingService:
    """
    Serviço que integra com a Booking.com API via RapidAPI (Provedor: DataCrawler / booking-com15).
    """
    def __init__(self):
        # Usando a chave já aprovada que o usuário possui
        self.api_key = settings.AERODATABOX_API_KEY 
        self.host = "booking-com15.p.rapidapi.com"
        self.base_url = f"https://{self.host}/api/v1"
        self.headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": self.host
        }

    def _get_dest_id(self, city_name: str) -> dict:
        """
        Busca o dest_id e search_type na API DataCrawler.
        """
        url = f"{self.base_url}/hotels/searchDestination"
        params = {"query": city_name}
        
        try:
            logger.debug(f"Buscando dest_id para: {city_name} (DataCrawler)")
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            
            if response.status_code != 200:
                logger.error(f"Erro ao buscar destino: {response.text}")
                return None
                
            data = response.json().get("data", [])
            
            if not data:
                return None
                
            # Preferir destino do tipo 'city'
            for loc in data:
                if loc.get("search_type") == "city":
                    logger.debug(f"Encontrado {loc.get('dest_id')} para {loc.get('search_type')}")
                    return {"dest_id": loc.get("dest_id"), "search_type": "city"}
            
            # Fallback para o primeiro
            return {"dest_id": data[0].get("dest_id"), "search_type": data[0].get("search_type")}
            
        except Exception as e:
            logger.error(f"Erro de conexão ao buscar dest_id: {e}")
            return None

    def search_hotels(self, city: str, checkin_date: str, checkout_date: str, adults: int = 2, rooms: int = 1) -> str:
        """
        Busca hotéis reais disponíveis usando a API-DOJO-like (DataCrawler).
        """
        location = self._get_dest_id(city)
        if not location:
            return f"Não foi possível encontrar a localização exata de '{city}' no Booking.com. Tente com SerpAPI."

        url = f"{self.base_url}/hotels/searchHotels"
        params = {
            "dest_id": location["dest_id"],
            "search_type": location["search_type"],
            "arrival_date": checkin_date,
            "departure_date": checkout_date,
            "adults": str(adults),
            "room_qty": str(rooms),
            "page_number": "1",
            "currency_code": "BRL",
            "languagecode": "pt-br"
        }

        try:
            logger.info(f"Buscando hotéis via DataCrawler para {city}")
            response = requests.get(url, headers=self.headers, params=params, timeout=20)
            
            if response.status_code != 200:
                logger.error(f"Erro na API de hotéis: {response.text}")
                return "Erro interno na busca de hotéis."

            response_data = response.json().get("data", {}).get("hotels", [])
            
            if not response_data:
                return f"Nenhum hotel disponível em {city} para as datas solicitadas."

            output = f"🏨 **Ofertas do Booking.com ({city})**\n\n"
            
            for idx, hotel_wrapper in enumerate(response_data[:5]):
                prop = hotel_wrapper.get("property", {})
                name = prop.get("name", "Desconhecido")
                score = prop.get("reviewScore", "N/A")
                
                # O preço da DataCrawler geralmente vem numa string concatenada e um objeto priceBreakdown
                price_breakdown = prop.get("priceBreakdown", {})
                gross_price = price_breakdown.get("grossPrice", {})
                price_str = f"{gross_price.get('currency', 'BRL')} {gross_price.get('value', 'Preço no link')}"
                
                if gross_price.get('value') is None:
                    # Fallback para acessibility label parsing se grossPrice falhar
                    label = hotel_wrapper.get("accessibilityLabel", "")
                    if "BRL" in label:
                        import re
                        match = re.search(r'(\d+)\s*BRL', label)
                        if match:
                            price_str = f"BRL {match.group(1)}"

                output += f"{idx + 1}. **{name}**\n"
                output += f"   - Avaliação: ⭐ {score}\n"
                output += f"   - Preço Est.: {price_str}\n"
                output += f"   - Link Rápido: [Ver no Booking](https://www.booking.com/hotel/br/{name.replace(' ', '-').lower()}.html)\n\n"

            return output

        except Exception as e:
            logger.error(f"Erro na parse dos hotéis: {e}")
            return f"Erro de processamento da resposta: {e}"
