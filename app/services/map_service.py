import json
import asyncio
from typing import List, Dict, Any, Optional
from loguru import logger
from app.config import settings
from app.services.openai_service import OpenAIService
from app.services.maps_service import GoogleMapsService
from app.services.rag_service import RAGService
from app.services.user_service import UserService

class InteractiveMapService:
    """
    Pilar 1: Cérebro de Extração Geoespacial
    Processa documentos RAG, extrai POIs com LLM e converte em Coordenadas Mapbox/Google.
    """
    
    def __init__(self):
        self.openai_svc = OpenAIService()
        self.maps_svc = GoogleMapsService()
        self.rag_svc = RAGService()
        self.user_svc = UserService()
        logger.info("🗺️ InteractiveMapService inicializado (Arquitetura Joule)")

    def _extract_locations_via_llm(self, rag_text: str) -> List[Dict[str, Any]]:
        """Usa a OpenAI para ler o RAG bruto e estruturar um JSON estrito de Localizações."""
        if not rag_text or len(rag_text.strip()) < 10:
            return []

        prompt = (
            "Você é um extrator geoespacial de elite (TravelConcierge System).\n"
            "Analise os documentos da viagem abaixo e extraia TODOS os locais físicos visitáveis (Aeroportos, Hotéis, Atrações, Eventos, Estações de Trem).\n"
            "Retorne ESTRITAMENTE um ARRAY JSON válido, onde cada objeto possua a exata estrutura:\n"
            "[\n"
            "  {\n"
            "    \"name\": \"Nome real do local (ex: The Ritz-Carlton Kyoto)\",\n"
            "    \"address\": \"Endereço ou cidade exata (usado no geocoding)\",\n"
            "    \"type\": \"hotel | airport | attraction | restaurant | transit\",\n"
            "    \"code\": \"Código de reserva ou N/A\",\n"
            "    \"documents\": [\"nome_do_arquivo.pdf se mencionado, ou vazio\"]\n"
            "  }\n"
            "]\n"
            f"DOCUMENTOS:\n---\n{rag_text}\n---"
        )

        try:
            from langchain_core.messages import SystemMessage
            # Usamos json_mode se o modelo suportar, mas para garantir, faremos parse
            response = self.openai_svc.llm.invoke([SystemMessage(content=prompt)])
            content = response.content
            
            # Limpar formatação Markdown se houver
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
                
            locations = json.loads(content)
            if isinstance(locations, list):
                return locations
            return []
            
        except json.JSONDecodeError as je:
            logger.error(f"Erro de Parse JSON na extração de mapas: {je}\nConteúdo: {content}")
            return []
        except Exception as e:
            logger.error(f"Erro na extração LLM para mapas: {e}")
            return []

    def get_trip_map_data(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Orquestra a coleta de dados de um determinado usuário, varrendo o RAG 
        (Cofre) exclusivo dele, extraindo via LLM e geocodificando via Google Maps.
        """
        # 1. Definir o Cofre da Viagem
        clean_uid = self.user_svc.normalize_phone(user_id)
        active_trip_id = self.user_svc.get_active_trip(clean_uid)
        
        if not active_trip_id:
            logger.warning(f"MapService: Nenhuma trip ativa para {clean_uid}")
            return []
            
        # 2. Resgatar os documentos textuais do Cofre no ChromaDB
        # A forma mais direta é usar as queries do RAG ou puxar os chunks brutos associados à trip.
        rag_context = ""
        user_docs = self.rag_svc.list_user_documents(clean_uid)
        
        if not user_docs:
            logger.info("MapService: Nenhum documento no RAG para mapear.")
            return []
            
        # Para forçar contexto máximo, pegamos os dados de todos os docs cadastrados na viagem
        # Fallback: Se não achar nada pelo trip_id, tenta pelo thread_id
        for doc in self.rag_svc.documents:
            meta = doc.get("metadata", {})
            m_trip = meta.get("trip_id")
            m_thread = self.user_svc.normalize_phone(meta.get("thread_id", ""))
            
            # Match 1: Trip ID perfeito
            # Match 2: Thread ID (usuário) for o mesmo e a trip for a ativa ou estiver vazia
            if m_trip == active_trip_id or (m_thread == clean_uid):
                # O text_content original fica em doc['text']
                rag_context += f"\nFile [{meta.get('filename', 'Unknown')}]:\n{doc.get('text', '')}"

        # 3. Processamento Neural (Backend Cérebro)
        extracted_locations = self._extract_locations_via_llm(rag_context)
        
        # 4. Geocodificação Precisa (Google Maps transformando texto em Lat/Lng)
        map_dataset = []
        for loc in extracted_locations:
            try:
                search_query = f"{loc.get('name', '')} {loc.get('address', '')}".strip()
                if not search_query:
                    continue
                    
                geo_result = self.maps_svc.geocode(search_query)
                if geo_result:
                    loc["lat"] = geo_result["lat"]
                    loc["lng"] = geo_result["lng"]
                    # Atualiza com endereço formatado real para polimento visual
                    loc["address"] = geo_result["formatted_address"]
                    map_dataset.append(loc)
                else:
                    logger.warning(f"Geocoding falhou para: {search_query}")
                    
            except Exception as geo_e:
                logger.error(f"Erro isolado no geocode de {loc}: {geo_e}")
                
        return map_dataset
