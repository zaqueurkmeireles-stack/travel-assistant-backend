"""
Scheduler Service - Gerencia tarefas agendadas para proatividade.
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import os
import json
from datetime import datetime
from app.services.trip_service import TripService
from app.services.n8n_service import N8nService
from app.services.weather_service import WeatherService
from app.services.connectivity_service import ConnectivityService
from loguru import logger

class SchedulerService:
    """Orquestra o envio de alertas proativos (D-7, D-1, D-0)"""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.trip_svc = TripService()
        self.n8n_svc = N8nService()
        self.weather_svc = WeatherService()
        self.conn_svc = ConnectivityService()
        logger.info("✅ SchedulerService inicializado")
        
    def start(self):
        """Inicia o cron job diário"""
        if not self.scheduler.running:
            # Executa a cada hora para checar alertas pendentes (ou uma vez por dia)
            # Para o MVP, checaremos a cada minuto durante o desenvolvimento/teste, 
            # mas em prod seria algo como 1x ao dia.
            self.scheduler.add_job(
                self.check_and_send_alerts,
                trigger=CronTrigger(hour=9, minute=0), # 9h da manhã todos os dias
                id="trip_alerts_check",
                replace_existing=True
            )
            # Periodic Audit - 10h da manhã
            self.scheduler.add_job(
                self.run_periodic_trip_audits,
                trigger=CronTrigger(hour=10, minute=0),
                id="trip_health_audit",
                replace_existing=True
            )
            self.scheduler.start()
            logger.info("⏰ Scheduler iniciado (Rodando verificação de alertas e auditoria)")

    def check_and_send_alerts(self):
        """Verifica quais viagens precisam de alerta hoje"""
        today = datetime.now()
        logger.info(f"⌛ Checando alertas para {today.date()}...")
        
        trips_to_alert = self.trip_svc.get_trips_to_alert(today)
        
        for trip in trips_to_alert:
            self._process_alert(trip)
            
        # [NOVO] Checar consumo de dados proativamente
        self.check_data_plans_proactively()

    def run_periodic_trip_audits(self):
        """Auditoria de saúde de todas as viagens ativas"""
        logger.info("🔍 Iniciando Auditoria de Saúde periódica das viagens...")
        from app.services.trip_audit_service import TripAuditService
        audit_svc = TripAuditService()
        
        for trip in self.trip_svc.trips:
            # Auditar apenas viagens futuras ou em andamento
            try:
                start_dt = datetime.strptime(trip["start_date"], "%Y-%m-%d").date()
                if start_dt >= datetime.now().date():
                    user_id = trip["user_id"]
                    audit_data = audit_svc.audit_trip(user_id, trip["id"], trip)
                    
                    # Só enviar se houver gaps relevantes
                    if audit_data.get("nights_covered", 0) < audit_data.get("trip_duration_days", 0) or audit_data.get("other_missing_items"):
                        report = audit_svc.generate_human_report(audit_data)
                        self.n8n_svc.enviar_resposta_usuario(user_id, report)
                        logger.info(f"📢 Relatório de Auditoria periódica enviado para {user_id}")
            except Exception as e:
                logger.error(f"Erro ao auditar trip {trip['id']} no scheduler: {e}")
            
    def _process_alert(self, trip: dict):
        """Processa e envia um alerta inteligente usando a IA"""
        alert_type = trip["pending_alert"]
        user_id = trip["user_id"]
        destination = trip["destination"]
        
        # Criar prompt contextual para a IA gerar o alerta
        prompt = (
            f"Você é o *Seven Assistant Travel*, o melhor concierge de viagens do mundo. "
            f"O usuário {user_id} tem uma viagem para {destination} em {trip['start_date']}.\n"
            f"Hoje estamos enviando o alerta tipo: **{alert_type}**.\n\n"
            f"Sua missão é gerar uma mensagem de WhatsApp extremamente útil, carinhosa e proativa baseada nos documentos dele no RAG.\n\n"
            "DIRETRIZES POR TIPO:\n"
            "- **D-7 (Uma semana antes)**: Anime o usuário! Mencione se falta algum documento (gap analysis). "
            "Pesquise se o destino (ou paradas intermediárias como Portugal/Europa) exige vistos/ETIAS e avise proativamente.\n"
            "- **D-1 (Véspera)**: Relembre o horário do voo e peça para fazer o CHECK-IN. "
            "Dê os CÓDIGOS DE RESERVA (localizadores) de todos os viajantes que encontrar.\n"
            "- **D-0 (Dia da Viagem)**: Comemore! 'Seu dia chegou!'. Informe o TERMINAL e o GUICHÊ DE CHECK-IN (se encontrar nos docs). "
            "Dê uma dica de como chegar ao aeroporto ou onde fica o guichê (ex: 'Vá até o guichê da TAP no Terminal 2').\n\n"
            "MUITO IMPORTANTE: Use apenas informações reais que encontrar no RAG. Se não encontrar o guichê, peça para ele verificar no painel mas diga o terminal."
        )
        
        try:
            from app.agents.orchestrator import TravelAgent
            agent = TravelAgent()
            # Usamos uma chamada interna que não salva no histórico de chat para não poluir
            ai_message = agent.chat(user_input=prompt, thread_id=user_id)
            
            if ai_message:
                logger.info(f"📨 Enviando alerta inteligente {alert_type} para {user_id}")
                self.n8n_svc.enviar_resposta_usuario(user_id, ai_message)
                self.trip_svc.mark_alert_sent(trip["id"], alert_type)
        except Exception as e:
            logger.error(f"❌ Falha ao gerar alerta inteligente: {e}")
            # Fallback para mensagem estática básica se a IA falhar
            fallback_msg = f"Olá! Falta pouco para sua viagem para {destination}. Estou aqui para ajudar!"
            self.n8n_svc.enviar_resposta_usuario(user_id, fallback_msg)

    def check_data_plans_proactively(self):
        """Verifica se algum plano de dados está chegando ao fim (10% alerta)"""
        # Simplificação: obter todos os planos em connectivity.json
        conn_db = os.path.join(os.path.dirname(self.trip_svc.db_path), "connectivity.json")
        if not os.path.exists(conn_db):
            return
            
        with open(conn_db, 'r', encoding='utf-8') as f:
            plans = json.load(f)
            
        for user_id, plan in plans.items():
            total = plan["total_gb"]
            # Estimar uso (exatamente como no service)
            registered_at = datetime.fromisoformat(plan["registered_at"])
            days_elapsed = (datetime.now() - registered_at).days + 1
            estimated_usage = min(days_elapsed * 0.5, total)
            remaining = total - estimated_usage
            percent = (remaining / total) * 100
            
            # Alerta crítico: 10% (e apenas uma vez, para não sobrecarregar)
            if percent <= 10 and plan.get("last_alert_sent") != "10%":
                message = (
                    f"⚠️ *Atenção, Zaqueu!* 📶\n"
                    f"Seu plano de dados de {total}GB está chegando ao fim. "
                    f"Resta apenas cerca de **{remaining:.2f}GB ({percent:.0f}%)**.\n\n"
                    "Gostaria que eu listasse opções de recarga agora?"
                )
                self.n8n_svc.enviar_resposta_usuario(user_id, message)
                plan["last_alert_sent"] = "10%"
                
                # Salvar marcação de alerta enviado
                plans[user_id] = plan
                with open(conn_db, 'w', encoding='utf-8') as f:
                    json.dump(plans, f, indent=2)
                logger.info(f"🚨 Alerta de 10% enviado para {user_id}")
