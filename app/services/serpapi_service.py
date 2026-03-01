"""
SerpApi Service - Acesso a dados do Google Flights, Hotels e Buscas
"""

import requests
from app.config import settings
from loguru import logger
from typing import List, Dict, Optional

class SerpApiService:
    """Service para integração com SerpApi (Google Professional Search)"""
    
    def __init__(self):
        """Inicializa o service"""
        self.api_key = settings.SERP_API_KEY
        self.base_url = "https://serpapi.com/search"
        
        if self.api_key:
            logger.info("✅ SerpApi Service inicializado")
        else:
            logger.warning("⚠️ Chave da SerpApi não configurada.")
            
    def search_hotels(self, city: str, check_in: str, check_out: str) -> str:
        """
        Busca hotéis reais via Google Hotels.
        check_in/check_out: YYYY-MM-DD
        """
        if not self.api_key:
            return "Busca de hotéis indisponível (Chave não configurada)."
            
        params = {
            "engine": "google_hotels",
            "q": city,
            "check_in_date": check_in,
            "check_out_date": check_out,
            "api_key": self.api_key,
            "hl": "pt",
            "gl": "br",
            "currency": "BRL"
        }
        
        try:
            logger.info(f"🏨 Buscando hotéis em {city}: {check_in} a {check_out}")
            response = requests.get(self.base_url, params=params, timeout=15)
            data = response.json()
            
            hotels = data.get("properties", [])
            
            if not hotels:
                return f"Nenhum hotel encontrado em {city} para as datas informadas."
                
            result = f"🏨 **Top Hotéis encontrados em {city}:**\n\n"
            
            for i, hotel in enumerate(hotels[:3], 1):
                name = hotel.get("name")
                price = hotel.get("rate_per_night", {}).get("lowest", "Preço sob consulta")
                rating = hotel.get("overall_rating", "N/A")
                amenities = ", ".join(hotel.get("amenities", [])[:5])
                
                result += f"{i}. **{name}**\n"
                result += f"   ⭐ Avaliação: {rating}\n"
                result += f"   💰 Tarifa: {price}\n"
                if amenities:
                    result += f"   ✨ Destaques: {amenities}\n"
                result += "\n"
                
            return result
            
        except Exception as e:
            logger.error(f"Erro ao buscar hotéis na SerpApi: {e}")
            return "Falha ao consultar hotéis no momento."

    def search_google_flights(self, origin: str, destination: str, date: str) -> str:
        """
        Busca voos via Google Flights (Complemento ao Duffel).
        """
        if not self.api_key:
            return "Busca do Google Flights indisponível."
            
        params = {
            "engine": "google_flights",
            "departure_id": origin,
            "arrival_id": destination,
            "outbound_date": date,
            "api_key": self.api_key,
            "currency": "BRL",
            "hl": "pt",
            "gl": "br"
        }
        
        try:
            logger.info(f"✈️ Buscando Google Flights: {origin} -> {destination}")
            response = requests.get(self.base_url, params=params, timeout=15)
            data = response.json()
            
            flights = data.get("best_flights", []) or data.get("other_flights", [])
            
            if not flights:
                return f"Nenhum voo encontrado no Google Flights entre {origin} e {destination}."
                
            result = f"✈️ **Opções via Google Flights ({origin} -> {destination}):**\n\n"
            
            for i, flight in enumerate(flights[:3], 1):
                airline = flight.get("flights", [{}])[0].get("airline")
                price = flight.get("price")
                duration = flight.get("total_duration")
                
                result += f"{i}. **{airline}**\n"
                result += f"   💰 Preço: R$ {price}\n"
                result += f"   🕒 Duração: {duration} min\n\n"
                
            return result
            
        except Exception as e:
            logger.error(f"Erro no Google Flights SerpApi: {e}")
            return "Erro ao consultar Google Flights."
    def search(self, query: str) -> str:
        """
        Realiza uma busca geral no Google via SerpApi.
        """
        if not self.api_key:
            return "Busca geral indisponível (Chave não configurada)."
            
        params = {
            "q": query,
            "api_key": self.api_key,
            "hl": "pt",
            "gl": "br"
        }
        
        try:
            logger.info(f"🔍 Buscando no Google: {query}")
            response = requests.get(self.base_url, params=params, timeout=15)
            data = response.json()
            
            results = data.get("organic_results", [])
            answer_box = data.get("answer_box", {})
            
            if not results and not answer_box:
                return "Nenhum resultado encontrado."
                
            res_text = ""
            if answer_box:
                res_text += f"Resposta Direta: {answer_box.get('answer') or answer_box.get('snippet')}\n\n"
                
            res_text += "Resultados da Busca:\n"
            for res in results[:5]:
                res_text += f"- {res.get('title')}: {res.get('snippet')} (Fonte: {res.get('link')})\n"
                
            return res_text
            
        except Exception as e:
            logger.error(f"Erro na busca geral SerpApi: {e}")
            return "Falha ao realizar busca no Google."
