"""Modelo de viagem"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class Trip(BaseModel):
    """Modelo de dados de uma viagem"""
    id: str = Field(..., description="ID único da viagem")
    user_id: str = Field(..., description="ID do usuário")
    destination: str = Field(..., description="Destino principal")
    start_date: datetime = Field(..., description="Data de início")
    end_date: datetime = Field(..., description="Data de término")
    status: str = Field(default="planning", description="Status da viagem")
    budget: Optional[float] = Field(None, description="Orçamento inicial")
    current_balance: Optional[float] = Field(None, description="Saldo atual dinâmico e disponível")
    drawdown: float = Field(default=0.0, description="Gastos e saques acumulados")
    travelers_count: int = Field(default=1, description="Número de viajantes")
