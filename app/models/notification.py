"""Modelo de notificação"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class Notification(BaseModel):
    """Modelo de notificação proativa"""
    id: str = Field(..., description="ID único")
    user_id: str = Field(..., description="ID do usuário")
    trip_id: str = Field(..., description="ID da viagem")
    message: str = Field(..., description="Mensagem da notificação")
    notification_type: str = Field(..., description="Tipo: reminder, alert, info")
    scheduled_time: datetime = Field(..., description="Horário agendado")
    sent: bool = Field(default=False, description="Se foi enviada")
    sent_at: Optional[datetime] = Field(None, description="Quando foi enviada")
