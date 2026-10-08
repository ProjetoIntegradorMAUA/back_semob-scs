from datetime import datetime

from pydantic import BaseModel


class FrotaHoraCreate(BaseModel):
    data: datetime
    hora: int
    mes: str
    numero_de_veiculos: int
    numero_de_viagens: int
