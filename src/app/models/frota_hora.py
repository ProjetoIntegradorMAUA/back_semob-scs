from datetime import datetime

from pydantic import BaseModel, Field


class FrotaHora(BaseModel):
    id: str = Field(alias="_id")
    data: datetime
    hora: int
    mes: str
    numero_de_veiculos: int
    numero_de_viagens: int
