"""Modelo de hotel"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class Hotel(BaseModel):
    """Modelo de reserva de hotel"""
    name: str = Field(..., description="Nome do hotel")
    address: str = Field(..., description="Endereço")
    check_in_date: datetime = Field(..., description="Data de check-in")
    check_out_date: datetime = Field(..., description="Data de check-out")
    reservation_code: str = Field(..., description="Código de reserva")
    contact_phone: Optional[str] = Field(None, description="Telefone do hotel")
