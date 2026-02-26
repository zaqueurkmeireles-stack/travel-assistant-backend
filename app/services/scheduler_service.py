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
                trigger=CronTrigger(minute="*"), # Checar a cada minuto para o MVP
                id="trip_alerts_check",
                replace_existing=True
            )
            self.scheduler.start()
            logger.info("⏰ Scheduler iniciado (Rodando verificação de alertas)")

    def check_and_send_alerts(self):
        """Verifica quais viagens precisam de alerta hoje"""
        today = datetime.now()
        logger.info(f"⌛ Checando alertas para {today.date()}...")
        
        trips_to_alert = self.trip_svc.get_trips_to_alert(today)
        
        for trip in trips_to_alert:
            self._process_alert(trip)
            
        # [NOVO] Checar consumo de dados proativamente para todos os usuários com planos ativos
        self.check_data_plans_proactively()
            
    def _process_alert(self, trip: dict):
        """Processa e envia um alerta inteligente usando a IA"""
        alert_type = trip["pending_alert"]
        user_id = trip["user_id"]
        destination = trip["destination"]
        
        # Criar prompt contextual para a IA gerar o alerta
        prompt = (
            f"Você é um Guia de Viagem VIP. O usuário {user_id} tem uma viagem para {destination} "
            f"em {trip['start_date']}. Hoje é o alerta tipo {alert_type}.\n"
            f"Consulte os documentos dele no RAG se necessário e gere uma mensagem de WhatsApp "
            f"EXTREMAMENTE útil, carinhosa e proativa. "
            f"Se for D-7, mencione vistos ou documentos se houver no RAG. "
            f"Se for D-1, lembre do check-in. "
            f"Se for D-0, dê as boas vindas e mencione o clima."
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
