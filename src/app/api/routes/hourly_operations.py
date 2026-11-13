from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pymongo.errors import DuplicateKeyError

from src.app.api.dependencies import get_current_user, get_hourly_operation_repository
from src.app.repositories.hourly_operation_repository import HourlyOperationRepository
from src.app.schemas.common import PaginationMeta
from src.app.schemas.hourly_operation import (
    HourlyOperationCreate,
    HourlyOperationList,
    HourlyOperationResponse,
    HourlyOperationUpdate,
)

router = APIRouter(prefix="/hourly-operations", tags=["Operação por hora"])


@router.post(
    "",
    response_model=HourlyOperationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_hourly_operation(
    data: HourlyOperationCreate,
    repository: Annotated[
        HourlyOperationRepository, Depends(get_hourly_operation_repository)
    ],
    _: Annotated[dict, Depends(get_current_user)],
):
    try:
        return repository.create(data.model_dump(mode="python"))
    except DuplicateKeyError as error:
        raise HTTPException(
            status_code=409,
            detail="Já existe uma operação para esta data, hora e linha.",
        ) from error


@router.get("", response_model=HourlyOperationList)
def list_hourly_operations(
    repository: Annotated[
        HourlyOperationRepository, Depends(get_hourly_operation_repository)
    ],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 30,
    start_date: date | None = None,
    end_date: date | None = None,
    line_code: str | None = None,
):
    items, total = repository.list(
        page, page_size, start_date, end_date, line_code
    )
    return HourlyOperationList(
        items=items,
        meta=PaginationMeta(page=page, page_size=page_size, total=total),
    )


@router.get("/{operation_id}", response_model=HourlyOperationResponse)
def get_hourly_operation(
    operation_id: str,
    repository: Annotated[
        HourlyOperationRepository, Depends(get_hourly_operation_repository)
    ],
):
    item = repository.get(operation_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Operação horária não encontrada.")
    return item


@router.patch("/{operation_id}", response_model=HourlyOperationResponse)
def update_hourly_operation(
    operation_id: str,
    data: HourlyOperationUpdate,
    repository: Annotated[
        HourlyOperationRepository, Depends(get_hourly_operation_repository)
    ],
    _: Annotated[dict, Depends(get_current_user)],
):
    try:
        item = repository.update(operation_id, data.model_dump(exclude_unset=True))
    except DuplicateKeyError as error:
        raise HTTPException(
            status_code=409,
            detail="Já existe uma operação para esta data, hora e linha.",
        ) from error
    if item is None:
        raise HTTPException(status_code=404, detail="Operação horária não encontrada.")
    return item


@router.delete("/{operation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_hourly_operation(
    operation_id: str,
    repository: Annotated[
        HourlyOperationRepository, Depends(get_hourly_operation_repository)
    ],
    _: Annotated[dict, Depends(get_current_user)],
):
    if repository.delete(operation_id) is None:
        raise HTTPException(status_code=404, detail="Operação horária não encontrada.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
