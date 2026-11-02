from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from src.app.api.dependencies import get_current_user, get_operation_repository
from src.app.repositories.operation_repository import OperationRepository
from src.app.schemas.common import PaginationMeta
from src.app.schemas.operation import OperationCreate, OperationList, OperationResponse, OperationUpdate

router = APIRouter(prefix="/operations", tags=["Operação"])


@router.post("", response_model=OperationResponse, status_code=status.HTTP_201_CREATED)
def create_operation(
    data: OperationCreate,
    repository: Annotated[OperationRepository, Depends(get_operation_repository)],
    _: Annotated[dict, Depends(get_current_user)],
):
    return repository.create(data.model_dump(mode="python"))


@router.get("", response_model=OperationList)
def list_operations(
    repository: Annotated[OperationRepository, Depends(get_operation_repository)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 30,
    start_date: date | None = None,
    end_date: date | None = None,
    line_code: str | None = None,
):
    items, total = repository.list(page, page_size, start_date, end_date, line_code)
    return OperationList(
        items=items,
        meta=PaginationMeta(page=page, page_size=page_size, total=total),
    )


@router.get("/{operation_id}", response_model=OperationResponse)
def get_operation(
    operation_id: str,
    repository: Annotated[OperationRepository, Depends(get_operation_repository)],
):
    item = repository.get(operation_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Registro operacional não encontrado.")
    return item


@router.patch("/{operation_id}", response_model=OperationResponse)
def update_operation(
    operation_id: str,
    data: OperationUpdate,
    repository: Annotated[OperationRepository, Depends(get_operation_repository)],
    _: Annotated[dict, Depends(get_current_user)],
):
    item = repository.update(operation_id, data.model_dump(exclude_unset=True))
    if item is None:
        raise HTTPException(status_code=404, detail="Registro operacional não encontrado.")
    return item


@router.delete("/{operation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_operation(
    operation_id: str,
    repository: Annotated[OperationRepository, Depends(get_operation_repository)],
    _: Annotated[dict, Depends(get_current_user)],
):
    if repository.delete(operation_id) is None:
        raise HTTPException(status_code=404, detail="Registro operacional não encontrado.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
