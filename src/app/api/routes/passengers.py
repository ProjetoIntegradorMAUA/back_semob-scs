from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from src.app.api.dependencies import get_current_user, get_passenger_repository
from src.app.repositories.passenger_repository import PassengerRepository
from src.app.schemas.common import PaginationMeta
from src.app.schemas.passenger import PassengerCreate, PassengerList, PassengerResponse, PassengerUpdate

router = APIRouter(prefix="/passengers", tags=["Passageiros"])


@router.post("", response_model=PassengerResponse, status_code=status.HTTP_201_CREATED)
def create_passenger(
    data: PassengerCreate,
    repository: Annotated[PassengerRepository, Depends(get_passenger_repository)],
    _: Annotated[dict, Depends(get_current_user)],
):
    return repository.create(data.model_dump(mode="python"))


@router.get("", response_model=PassengerList)
def list_passengers(
    repository: Annotated[PassengerRepository, Depends(get_passenger_repository)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 30,
    start_date: date | None = None,
    end_date: date | None = None,
):
    items, total = repository.list(page, page_size, start_date, end_date)
    return PassengerList(
        items=items,
        meta=PaginationMeta(page=page, page_size=page_size, total=total),
    )


@router.get("/{passenger_id}", response_model=PassengerResponse)
def get_passenger(
    passenger_id: str,
    repository: Annotated[PassengerRepository, Depends(get_passenger_repository)],
):
    item = repository.get(passenger_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Registro de passageiros não encontrado.")
    return item


@router.patch("/{passenger_id}", response_model=PassengerResponse)
def update_passenger(
    passenger_id: str,
    data: PassengerUpdate,
    repository: Annotated[PassengerRepository, Depends(get_passenger_repository)],
    _: Annotated[dict, Depends(get_current_user)],
):
    item = repository.update(passenger_id, data.model_dump(exclude_unset=True))
    if item is None:
        raise HTTPException(status_code=404, detail="Registro de passageiros não encontrado.")
    return item


@router.delete("/{passenger_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_passenger(
    passenger_id: str,
    repository: Annotated[PassengerRepository, Depends(get_passenger_repository)],
    _: Annotated[dict, Depends(get_current_user)],
):
    if repository.delete(passenger_id) is None:
        raise HTTPException(status_code=404, detail="Registro de passageiros não encontrado.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
