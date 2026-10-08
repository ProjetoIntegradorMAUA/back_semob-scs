from fastapi import APIRouter, HTTPException

from src.app.repositories.frota_hora import create_frota_hora
from src.app.schemas.frota_hora import FrotaHoraCreate

router = APIRouter(prefix="/api/frotahora")


@router.post("/create", status_code=201)
def criar_frota_hora(frota: FrotaHoraCreate):
    dados = frota.model_dump()
    frota_id = create_frota_hora(dados=dados)
    if frota_id is None:
        raise HTTPException(404, detail="Erro ao criar frota por hora.")
    return {
        "id": frota_id,
        "data": frota.data,
        "hora": frota.hora,
        "mes": frota.mes,
        "numero_de_veiculos": frota.numero_de_veiculos,
        "numero_de_viagens": frota.numero_de_viagens,
    }
