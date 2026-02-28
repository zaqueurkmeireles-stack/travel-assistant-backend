"""
Emergency Service - Provedor de números de emergência locais por país.
"""

from loguru import logger
from typing import Dict, Optional

class EmergencyService:
    """Service para fornecer números de Polícia, Ambulância e Bombeiros ao redor do mundo"""
    
    # Mapeamento básico de países comuns (fallback rápido)
    EMERGENCY_DATA = {
        "Brasil": {"police": "190", "ambulance": "192", "fire": "193", "general": "190"},
        "USA": {"police": "911", "ambulance": "911", "fire": "911", "general": "911"},
        "Portugal": {"police": "112", "ambulance": "112", "fire": "112", "general": "112"},
        "Alemanha": {"police": "110", "ambulance": "112", "fire": "112", "general": "112"},
        "Espanha": {"police": "091", "ambulance": "061", "fire": "080", "general": "112"},
        "França": {"police": "17", "ambulance": "15", "fire": "18", "general": "112"},
        "Itália": {"police": "113", "ambulance": "118", "fire": "115", "general": "112"},
        "Reino Unido": {"police": "999", "ambulance": "999", "fire": "999", "general": "999"},
        "Argentina": {"police": "101", "ambulance": "107", "fire": "100", "general": "911"},
    }

    def get_numbers(self, country: str) -> Dict[str, str]:
        """Retorna números de emergência para um país específico"""
        logger.info(f"🚑 Buscando números de emergência para: {country}")
        
        # Limpeza simples do nome do país
        country_clean = country.strip().capitalize()
        
        if country_clean in self.EMERGENCY_DATA:
            return self.EMERGENCY_DATA[country_clean]
        
        # Se não estiver no mapa, tenta uma busca proativa via internet (SearchService)
        try:
            from app.services.search_service import SearchService
            search = SearchService()
            query = f"emergency numbers police ambulance fire in {country}"
            result = search.search_real_experiences(country, "emergency numbers")
            
            # Nota: No futuro, poderíamos usar um parser de IA aqui para extrair os números do texto
            return {
                "info": result,
                "note": "Números obtidos via busca em tempo real. Por favor, verifique localmente se possível."
            }
        except Exception as e:
            logger.error(f"Erro ao buscar números de emergência via web: {e}")
            return {"general": "112", "note": "Use o número universal 112 se estiver na Europa ou tente 911."}

    def format_emergency_message(self, country: str, numbers: Dict[str, str]) -> str:
        """Formata a mensagem de socorro para o WhatsApp"""
        msg = f"🚨 *PROTOCOLO DE EMERGÊNCIA ATIVADO: {country.upper()}* 🚨\n\n"
        
        if "info" in numbers:
            msg += f"Encontrei as seguintes informações para {country}:\n{numbers['info']}\n"
        else:
            msg += f"📞 **Polícia:** {numbers.get('police', '112')}\n"
            msg += f"🚑 **Ambulância:** {numbers.get('ambulance', '112')}\n"
            msg += f"🚒 **Bombeiros:** {numbers.get('fire', '112')}\n"
            if numbers.get("general") and numbers["general"] != numbers.get("police"):
                msg += f"🆘 **Geral:** {numbers['general']}\n"
        
        msg += "\n⚠️ *Mantenha a calma. O Seven Assistant está aqui com você.*"
        return msg
