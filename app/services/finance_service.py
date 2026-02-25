"""
Finance Service - Conversão de moedas e dicas financeiras
"""

import requests
from loguru import logger
from typing import Dict, Optional

class FinanceService:
    """Service para conversão de moedas e dicas de câmbio"""
    
    def __init__(self):
        # Usando Frankfurter API como fallback gratuito (não requer chave)
        self.base_url = "https://api.frankfurter.app"
        logger.info("✅ Finance Service inicializado (Frankfurter API)")
        
    def convert_currency(self, amount: float, from_curr: str, to_curr: str) -> str:
        """
        Converte um valor entre moedas (ex: USD para BRL).
        """
        try:
            from_curr = from_curr.upper()
            to_curr = to_curr.upper()
            
            if from_curr == to_curr:
                return f"{amount} {from_curr} é igual a {amount} {to_curr}."
                
            logger.info(f"💸 Convertendo {amount} {from_curr} para {to_curr}")
            
            url = f"{self.base_url}/latest?amount={amount}&from={from_curr}&to={to_curr}"
            response = requests.get(url, timeout=10)
            data = response.json()
            
            if response.status_code == 200:
                converted_amount = data.get("rates", {}).get(to_curr)
                date = data.get("date")
                return f"💰 **Conversão Atual ({date}):**\n{amount} {from_curr} = **{converted_amount:.2f} {to_curr}**."
            else:
                return f"Não foi possível converter de {from_curr} para {to_curr} no momento."
                
        except Exception as e:
            logger.error(f"Erro no FinanceService: {e}")
            return "Erro ao realizar conversão de moeda."

    def get_exchange_tips(self, destination: str) -> str:
        """Dicas rápidas de câmbio para o destino."""
        # Lógica simples para o MVP
        return (
            f"💡 **Dica de Câmbio para {destination}:**\n"
            "- Evite trocar dinheiro em aeroportos (taxas piores).\n"
            "- Use cartões globais (Wise, Nomad) para IOF mais baixo (1.1%).\n"
            "- Tenha sempre uma pequena quantia em dinheiro vivo para emergências."
        )
