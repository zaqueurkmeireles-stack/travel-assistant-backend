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
            
        trip_id = f"{user_id}_{destination.upper()}_{start_date}"
        
        # Verificar se já existe
        for trip in self.trips:
            if trip["id"] == trip_id:
                # Atualizar end_date se vier no novo doc e não tiver no antigo
                if doc_data.get("end_date") and not trip.get("end_date"):
                    trip["end_date"] = doc_data.get("end_date")
                
                # [NOVO] Acumular POIs (Pontos de Interesse) de docs diferentes
                new_pois = doc_data.get("points_of_interest", [])
                if new_pois:
                    existing_pois = trip.get("points_of_interest", [])
                    # Union of lists avoiding duplicates
                    trip["points_of_interest"] = list(set(existing_pois + new_pois))
                
                self._save_trips()
                return trip
                
        new_trip = {
            "id": trip_id,
            "user_id": user_id,
            "destination": destination,
            "start_date": start_date,
            "end_date": doc_data.get("end_date"),
            "confirmation_code": doc_data.get("confirmation_code"),
            "flight_number": doc_data.get("flight_number"), 
            "event_name": doc_data.get("event_name"), # Novo: Para F1/Shows
            "venue": doc_data.get("venue"),           
            "gate": doc_data.get("gate"),             
            "points_of_interest": doc_data.get("points_of_interest", []), # Lista de locais (ex: Parques Estaduais)
            "alerts_sent": [], 
            "landing_alert_sent": False, 
            "created_at": datetime.now().isoformat()
        }
        
        self.trips.append(new_trip)
        self._save_trips()
        logger.info(f"✨ Nova viagem agendada: {destination} em {start_date}")
        return new_trip

    def register_data_plan(self, user_id: str, total_gb: float, duration_days: int):
        """Registra um plano de dados para o usuário na viagem atual ou futura"""
        # Simplificação: assume o plano para a viagem mais próxima
        plan = {
            "user_id": user_id,
            "total_gb": total_gb,
            "used_gb": 0.0,
            "duration_days": duration_days,
            "registered_at": datetime.now().isoformat(),
            "last_screenshot_sync": None
        }
        
        # Salva em um arquivo separado ou no trips.json (usaremos db_connectivity.json para separar responsabilidades)
        conn_db = os.path.join(os.path.dirname(self.db_path), "connectivity.json")
        data = {}
        if os.path.exists(conn_db):
            with open(conn_db, 'r', encoding='utf-8') as f:
                data = json.load(f)
        
        data[user_id] = plan
        with open(conn_db, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"📶 Plano de {total_gb}GB registrado para {user_id}")
        return plan

    def get_data_plan(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Recupera o plano de dados ativo do usuário"""
        conn_db = os.path.join(os.path.dirname(self.db_path), "connectivity.json")
        if not os.path.exists(conn_db):
            return None
            
        with open(conn_db, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get(user_id)

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
                    # Lógica Extra: Se for D-1, verificar necessidade de mapas offline
                    if alert_type == "D-1":
                        trip["needs_offline_map_check"] = True
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
    def get_shared_users(self, user_id: str) -> List[str]:
        """Retorna outros usuários que compartilham viagens com este usuário"""
        shared_users = []
        user_trips = [t.get("confirmation_code") for t in self.trips if t["user_id"] == user_id and t.get("confirmation_code")]
        
        if not user_trips:
            return []
            
        for trip in self.trips:
            if trip["user_id"] != user_id and trip.get("confirmation_code") in user_trips:
                # Verificar se o compartilhamento foi aceito (poderia ter um flag 'shared_with': [user_ids])
                if user_id in trip.get("shared_with", []):
                    shared_users.append(trip["user_id"])
                    
        return list(set(shared_users))

    def request_trip_sharing(self, user_id: str, confirmation_code: str, partner_id: str):
        """Registra uma solicitação ou aceite de compartilhamento"""
        for trip in self.trips:
            if trip["user_id"] == user_id and trip.get("confirmation_code") == confirmation_code:
                if "shared_with" not in trip:
                    trip["shared_with"] = []
                if partner_id not in trip["shared_with"]:
                    trip["shared_with"].append(partner_id)
                    self._save_trips()
                return True
        return False

    def find_potential_partner(self, user_id: str, confirmation_code: str) -> Optional[str]:
        """Procura outro usuário com o mesmo código de reserva"""
        for trip in self.trips:
            if trip["user_id"] != user_id and trip.get("confirmation_code") == confirmation_code:
                return trip["user_id"]
        return None

    def find_similar_trips(self, exclude_user_id: str, destination: str, start_date: str) -> Optional[Dict[str, Any]]:
        """Busca viagens de outros usuários com mesmo destino e data próxima (±3 dias).
        Retorna a trip e o user_id do dono caso encontre match."""
        if not destination or not start_date:
            return None
        try:
            from datetime import timedelta
            target_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        except Exception:
            return None

        dest_lower = destination.lower().strip()
        for trip in self.trips:
            if trip["user_id"] == exclude_user_id:
                continue
            try:
                trip_dest = trip.get("destination", "").lower().strip()
                trip_date = datetime.strptime(trip["start_date"], "%Y-%m-%d").date()
                date_diff = abs((target_date - trip_date).days)
                # Match se destino contém pelo menos 4 chars em comum e data com diferença <= 3 dias
                dest_match = dest_lower[:4] in trip_dest or trip_dest[:4] in dest_lower
                if dest_match and date_diff <= 3:
                    logger.info(f"🔗 Viagem similar encontrada: {trip['id']} (diff={date_diff} dias)")
                    return {"trip": trip, "host_user_id": trip["user_id"]}
            except Exception:
                continue
        return None
    def get_active_monitoring_trips(self, today: datetime) -> List[Dict[str, Any]]:
        """
        Retorna viagens que estão na janela de monitoramento proativo (D-7 até a data de término).
        Útil para alertas de notícias, segurança e avisos governamentais.
        """
        active_trips = []
        today_date = today.date()
        
        for trip in self.trips:
            try:
                start_dt = datetime.strptime(trip["start_date"], "%Y-%m-%d").date()
                end_date_str = trip.get("end_date")
                
                if end_date_str:
                    end_dt = datetime.strptime(end_date_str, "%Y-%m-%d").date()
                else:
                    # Se não tiver data de término, assume 1 dia após o início
                    from datetime import timedelta
                    end_dt = start_dt + timedelta(days=1)
                
                # Janela: 7 dias antes do início até o fim da viagem
                from datetime import timedelta
                monitoring_start = start_dt - timedelta(days=7)
                
                if monitoring_start <= today_date <= end_dt:
                    active_trips.append(trip)
                    
            except Exception as e:
                logger.error(f"Erro ao calcular janela de monitoramento para trip {trip.get('id')}: {e}")
                
        return active_trips
