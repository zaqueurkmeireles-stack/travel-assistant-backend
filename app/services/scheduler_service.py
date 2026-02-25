"""
Scheduler Service - Gerencia tarefas agendadas para proatividade.
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from app.services.trip_service import TripService
from app.services.n8n_service import N8nService
from app.services.weather_service import WeatherService
from loguru import logger

class SchedulerService:
    """Orquestra o envio de alertas proativos (D-7, D-1, D-0)"""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.trip_svc = TripService()
        self.n8n_svc = N8nService()
        self.weather_svc = WeatherService()
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
            
    def _process_alert(self, trip: dict):
        """Processa e envia um alerta específico"""
        alert_type = trip["pending_alert"]
        user_id = trip["user_id"]
        destination = trip["destination"]
        
        message = ""
        if alert_type == "D-7":
            message = f"🌟 *Falta 1 semana para sua viagem para {destination}!* ✈️\nNão esqueça de verificar seu passaporte e começar a organizar as malas. Precisa de alguma dica de última hora?"
        
        elif alert_type == "D-1":
            message = f"🎒 *Sua viagem para {destination} é AMANHÃ!* 🕒\nLembre-se de fazer o check-in. Gostaria que eu verificasse o status do seu voo?"
        
        elif alert_type == "D-0":
            # Obter clima para o dia
            weather_info = ""
            try:
                weather = self.weather_svc.get_current_weather(destination)
                if weather:
                    weather_info = f"\n🌤️ O clima em {destination} agora: {weather['temperature']}°C, {weather['description']}."
            except: pass
            
            message = f"🚀 *É HOJE! Boa viagem para {destination}!* 🌍\nJá estou a postos para te ajudar com qualquer dúvida ou localização.{weather_info}\n\nBoa jornada para você e sua família! ❤️"

        if message:
            logger.info(f"📨 Enviando alerta {alert_type} para {user_id}")
            self.n8n_svc.enviar_resposta_usuario(user_id, message)
            self.trip_svc.mark_alert_sent(trip["id"], alert_type)
