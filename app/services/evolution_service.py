import httpx
from loguru import logger
from app.config import settings

class EvolutionService:
    def __init__(self):
        self.base_url = settings.EVOLUTION_API_URL
        self.api_key = settings.EVOLUTION_API_KEY
        self.instance = settings.EVOLUTION_INSTANCE_NAME

    async def send_text(self, number: str, text: str):
        url = f"{self.base_url}/message/sendText/{self.instance}"
        headers = {"apikey": self.api_key, "Content-Type": "application/json"}
        payload = {"number": number, "text": text}
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload, headers=headers)
                if response.status_code in [200, 201]:
                    logger.info(f"✅ Mensagem enviada para {number}")
                else:
                    logger.error(f"❌ Erro Evolution: {response.text}")
            except Exception as e:
                logger.error(f"❌ Falha de conexão com Evolution: {e}")
