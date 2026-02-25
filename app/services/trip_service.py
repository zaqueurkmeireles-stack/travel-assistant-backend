"""
Trip Service - Gerencia o banco de dados de viagens para o scheduler.
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from app.config import settings
from loguru import logger

class TripService:
    """Gerencia viagens extraídas de documentos para alertas proativos"""
    
    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(settings.CHROMA_DB_PATH), "trips.json")
        self.trips = []
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._load_trips()
        logger.info(f"✅ TripService inicializado (Base: {self.db_path})")
        
    def _load_trips(self):
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, 'r', encoding='utf-8') as f:
                    self.trips = json.load(f)
                logger.info(f"📅 {len(self.trips)} viagens carregadas para monitoramento.")
            except Exception as e:
                logger.error(f"Erro ao carregar viagens: {e}")
                
    def _save_trips(self):
        try:
            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump(self.trips, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Erro ao salvar viagens: {e}")

    def add_trip_from_doc(self, user_id: str, doc_data: Dict[str, Any]):
        """Adiciona ou atualiza uma viagem com base no parse do documento"""
        start_date = doc_data.get("start_date")
        destination = doc_data.get("destination")
        
        if not start_date or not destination:
            return None
            
        trip_id = f"{user_id}_{destination}_{start_date}"
        
        # Verificar se já existe
        for trip in self.trips:
            if trip["id"] == trip_id:
                logger.info(f"Trip {trip_id} já existe, ignorando duplicata.")
                return trip
                
        new_trip = {
            "id": trip_id,
            "user_id": user_id,
            "destination": destination,
            "start_date": start_date,
            "end_date": doc_data.get("end_date"),
            "confirmation_code": doc_data.get("confirmation_code"),
            "alerts_sent": [], # Lista de tipos de alertas já enviados: ["D-7", "D-1", "D-0"]
            "created_at": datetime.now().isoformat()
        }
        
        self.trips.append(new_trip)
        self._save_trips()
        logger.info(f"✨ Nova viagem agendada: {destination} em {start_date}")
        return new_trip

    def get_trips_to_alert(self, today: datetime) -> List[Dict[str, Any]]:
        """Retorna viagens que precisam de alerta hoje e ainda não foram notificadas"""
        trips_to_notify = []
        
        for trip in self.trips:
            try:
                start_dt = datetime.strptime(trip["start_date"], "%Y-%m-%d").date()
                today_date = today.date()
                delta_days = (start_dt - today_date).days
                
                logger.debug(f"Trip {trip['id']}: {delta_days} dias para embarque.")
                
                alert_type = None
                if delta_days == 7: alert_type = "D-7"
                elif delta_days == 1: alert_type = "D-1"
                elif delta_days == 0: alert_type = "D-0"
                
                if alert_type and alert_type not in trip.get("alerts_sent", []):
                    trip["pending_alert"] = alert_type
                    trips_to_notify.append(trip)
            except Exception as e:
                logger.error(f"Erro ao processar data da viagem {trip['id']}: {e}")
                
        return trips_to_notify

    def mark_alert_sent(self, trip_id: str, alert_type: str):
        """Marca que um alerta foi enviado para evitar repetição"""
        for trip in self.trips:
            if trip["id"] == trip_id:
                if "alerts_sent" not in trip:
                    trip["alerts_sent"] = []
                trip["alerts_sent"].append(alert_type)
                self._save_trips()
                break
