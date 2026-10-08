from fastapi import APIRouter, HTTPException

from src.app.schemas.frota_hora import FrotaHoraCreate

router = APIRouter(prefix="/api/frotahora")

@router.post("/create", status_code=201)
def criar_frota_hora(frota:FrotaHoraCreate):
    pass