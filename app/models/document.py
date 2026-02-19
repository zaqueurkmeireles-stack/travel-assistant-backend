"""Modelo de documento de viagem"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class TravelDocument(BaseModel):
    """Modelo de documento de viagem"""
    id: str = Field(..., description="ID único do documento")
    trip_id: str = Field(..., description="ID da viagem")
    document_type: str = Field(..., description="Tipo: passport, visa, ticket, hotel, insurance")
    file_path: str = Field(..., description="Caminho do arquivo")
    extracted_text: Optional[str] = Field(None, description="Texto extraído")
    uploaded_at: datetime = Field(default_factory=datetime.now, description="Data de upload")
