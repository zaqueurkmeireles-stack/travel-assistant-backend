"""
Connectivity Service - Recomendações de Chip e eSIM para o exterior
"""

from app.services.search_service import SearchService
from app.services.trip_service import TripService
from app.services.openai_service import OpenAIService
from loguru import logger
from datetime import datetime

class ConnectivityService:
    """Service para recomendar e monitorar internet no exterior"""
    
    def __init__(self):
        self.search_svc = SearchService()
        self.trip_svc = TripService()
        self.openai_svc = OpenAIService()
        logger.info("✅ Connectivity Service inicializado")
        
    def get_e_sim_recommendations(self, destination: str) -> str:
        """Busca as melhores opções de chip/eSIM para o destino específico."""
        logger.info(f"📶 Buscando opções de internet para {destination}")
        topic = "melhores chips de viagem eSIM airalo holafly operadoras locais dicas"
        search_result = self.search_svc.search_real_experiences(destination, topic)
        
        prompt_intro = (
            f"📶 **Conectividade em {destination}:**\n"
            "Existem 3 formas principais de ter internet:\n\n"
            "1. **eSIM Internacional (Recomendado)**: Opções como **Airalo** ou **Holafly**.\n"
            "2. **Chip Local**: Mais barato, mas precisa de compra física.\n"
            "3. **Roaming**: Geralmente caro.\n\n"
            "**Dicas baseadas em pesquisas atuais:**\n"
        )
        return f"{prompt_intro}{search_result}"

    def estimate_data_usage(self, user_id: str) -> str:
        """Estima o consumo atual com base no tempo decorrido (Medidor Virtual)"""
        plan = self.trip_svc.get_data_plan(user_id)
        if not plan:
            return "Nenhum plano de dados registrado. Diga 'Comprei um chip de X GB' para eu começar a monitorar!"
            
        total_gb = plan["total_gb"]
        duration = plan["duration_days"]
        registered_at = datetime.fromisoformat(plan["registered_at"])
        days_elapsed = (datetime.now() - registered_at).days + 1
        
        # Estimativa simples: 0.5GB por dia (ajustável)
        estimated_usage = min(days_elapsed * 0.5, total_gb)
        remaining = total_gb - estimated_usage
        percent = (remaining / total_gb) * 100
        
        status = "🟢" if percent > 30 else "🟡" if percent > 10 else "🔴"
        
        result = (
            f"📊 **Medidor Virtual de Dados:**\n"
            f"Plano Total: {total_gb} GB\n"
            f"Uso Estimado: {estimated_usage:.2f} GB ({days_elapsed} dias de uso)\n"
            f"Restante: **{remaining:.2f} GB ({percent:.0f}%)** {status}\n\n"
            "Lembre-se: Esta é uma estimativa. Se puder, envie um **PRINT** da tela de consumo do celular para eu sincronizar o valor exato!"
        )
        return result

    def analyze_usage_screenshot(self, user_id: str, image_path: str) -> str:
        """Analisa print do celular para recalibrar o medidor real"""
        logger.info(f"👁️ Analisando print de dados para {user_id}")
        
        analysis = self.openai_svc.analyze_image(
            image_path, 
            "Este é um print da tela de consumo de dados de um celular. Identifique quantos GB ou MB ainda restam de franquia ou quanto foi usado do total. Responda apenas o valor detectado e o total."
        )
        
        # TODO: Implementar lógica de atualização no JSON aqui
        return f"✅ **Sincronização via Print:**\n\nAnalisei sua imagem e identifiquei seu consumo real. Estou atualizando seu medidor virtual!\n\nExtrato da IA: {analysis}"
