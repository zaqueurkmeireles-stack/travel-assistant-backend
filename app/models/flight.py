"""Modelo de voo"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class Flight(BaseModel):
    """Modelo de dados de voo"""
    flight_number: str = Field(..., description="Número do voo")
    airline: str = Field(..., description="Companhia aérea")
    departure_airport: str = Field(..., description="Aeroporto de origem")
    arrival_airport: str = Field(..., description="Aeroporto de destino")
    departure_time: datetime = Field(..., description="Horário de partida")
    arrival_time: datetime = Field(..., description="Horário de chegada")
    gate: Optional[str] = Field(None, description="Portão de embarque")
    status: str = Field(default="scheduled", description="Status do voo")
