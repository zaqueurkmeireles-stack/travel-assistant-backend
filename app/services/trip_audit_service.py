"""
Trip Audit Service - Inteligência Proativa para lacunas de viagem.
Analisa a cobertura de hotéis, voos e roteiros.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from loguru import logger
from app.services.rag_service import RAGService
from app.services.openai_service import OpenAIService

class TripAuditService:
    """Service para auditar a 'saúde' da viagem e encontrar documentos faltantes"""
    
    def __init__(self):
        self.rag_svc = RAGService()
        self.openai_svc = OpenAIService()

    def audit_trip(self, user_id: str, trip_id: str, trip_info: Dict[str, Any]) -> Dict[str, Any]:
        """Realiza auditoria completa da viagem"""
        logger.info(f"🧐 Auditando viagem {trip_id} para o usuário {user_id}")
        
        start_date_str = trip_info.get("start_date")
        end_date_str = trip_info.get("end_date")
        destination = trip_info.get("destination", "seu destino")
        
        if not start_date_str or not end_date_str:
            return {"success": False, "error": "Datas de início ou fim incompletas para auditoria."}

        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except Exception as e:
            return {"success": False, "error": f"Erro no formato das datas: {e}"}

        total_days = (end_date - start_date).days
        total_nights = total_days # Assumindo noites = dias entre datas
        
        # 1. Buscar todos os documentos do usuário para esta viagem no RAG
        # Vamos usar a query semântica para pegar o que parece ser reserva de hotel
        hotel_context = self.rag_svc.query("reservas de hotel, hospedagem, check-in, check-out", user_id, k=10)
        
        # 2. Usar LLM para extrair as noites cobertas
        prompt = (
            f"Analise o texto abaixo de documentos de viagem do usuário para a viagem a {destination}.\n"
            f"A viagem vai de {start_date_str} até {end_date_str} ({total_nights} noites).\n"
            f"Extraia TODAS as noites que possuem reserva confirmada de hotel.\n"
            f"Retorne um JSON estritamente no formato:\n"
            "{\n"
            "  \"nights_covered\": [\"YYYY-MM-DD\", ...],\n"
            "  \"total_nights_covered\": 0,\n"
            "  \"missing_nights\": [\"YYYY-MM-DD\", ...],\n"
            "  \"other_missing_items\": [\"seguro viagem\", \"aluguel de carro\", ...]\n"
            "}\n"
            "Considere apenas datas dentro do intervalo da viagem."
        )
        
        messages = [
            {"role": "system", "content": "Você é um auditor de viagens meticuloso. Encontre lacunas no planejamento."},
            {"role": "user", "content": f"{prompt}\n\nDOCUMENTOS:\n{hotel_context}"}
        ]
        
        response = self.openai_svc.chat_completion(messages, temperature=0.1, response_format={"type": "json_object"})
        
        try:
            audit_result = json.loads(response)
            audit_result["trip_duration_days"] = total_days
            audit_result["destination"] = destination
            
            # Adicionar lógica de "Checklist do Roteiro" se houver documento de roteiro
            itinerary_context = self.rag_svc.query("roteiro de viagem, itinerário, o que fazer em cada dia", user_id, k=3)
            if itinerary_context and len(itinerary_context) > 100:
                itinerary_prompt = (
                    "Com base no roteiro abaixo, extraia uma lista de itens que o usuário PRECISA ter reserva "
                    "(ex: ingressos, tours, transfers) mas que NÃO parecem estar confirmados nos documentos.\n"
                    "Retorne em uma lista 'itinerary_gaps'."
                )
                itinerary_msg = [
                    {"role": "system", "content": "Você é um especialista em roteiros."},
                    {"role": "user", "content": f"{itinerary_prompt}\n\nROTEIRO:\n{itinerary_context}"}
                ]
                itin_resp = self.openai_svc.chat_completion(itinerary_msg, temperature=0.1, response_format={"type": "json_object"})
                itin_data = json.loads(itin_resp)
                audit_result["itinerary_gaps"] = itin_data.get("itinerary_gaps", [])

            return audit_result
        except Exception as e:
            logger.error(f"Erro ao processar auditoria do LLM: {e}")
            return {"success": False, "error": "Falha ao processar auditoria inteligente."}

    def generate_human_report(self, audit_data: Dict[str, Any]) -> str:
        """Transforma os dados da auditoria em uma mensagem amigável para o WhatsApp"""
        dest = audit_data.get("destination", "sua viagem")
        nights_covered = audit_data.get("total_nights_covered", 0)
        total_nights = audit_data.get("trip_duration_days", 0)
        missing_nights = audit_data.get("missing_nights", [])
        other_missing = audit_data.get("other_missing_items", [])
        itin_gaps = audit_data.get("itinerary_gaps", [])

        if nights_covered >= total_nights and not other_missing and not itin_gaps:
            return f"✅ *Auditoria de Viagem: {dest}*\n\nRodrigo, analisei tudo e seu planejamento está nota 10! Todas as noites e documentos essenciais estão garantidos. Boa viagem! ✈️"

        report = f"⚠️ *Auditoria de Viagem: {dest}*\n\nAnalisei seu roteiro e notei alguns pontos que faltam:\n"
        
        if nights_covered < total_nights:
            report += f"- *Hospedagem:* Sua viagem tem {total_nights} noites, mas só encontrei reserva para {nights_covered}. "
            if missing_nights:
                report += f"Faltam as noites de: {', '.join(missing_nights[:3])}..."
            report += "\n"

        if other_missing:
            report += f"- *Essenciais:* Não vi documentos de: {', '.join(other_missing)}.\n"

        if itin_gaps:
            report += f"- *Do seu Roteiro:* Notei que você planejou {', '.join(itin_gaps[:3])} mas ainda não me enviou as confirmações.\n"

        report += "\n💡 *Dica:* Se você já tiver esses documentos, basta me enviar o PDF ou print aqui que eu atualizo tudo!"
        
        return report
