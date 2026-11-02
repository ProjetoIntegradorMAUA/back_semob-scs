from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from src.app.api.dependencies import get_current_user, get_financial_repository
from src.app.repositories.financial_repository import FinancialRepository
from src.app.schemas.common import PaginationMeta
from src.app.schemas.financial import FinancialCreate, FinancialList, FinancialResponse, FinancialUpdate

router = APIRouter(prefix="/financials", tags=["Financeiro"])


@router.post("", response_model=FinancialResponse, status_code=status.HTTP_201_CREATED)
def create_financial(
    data: FinancialCreate,
    repository: Annotated[FinancialRepository, Depends(get_financial_repository)],
    _: Annotated[dict, Depends(get_current_user)],
):
    return repository.create(data.model_dump(mode="python"))


@router.get("", response_model=FinancialList)
def list_financials(
    repository: Annotated[FinancialRepository, Depends(get_financial_repository)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 30,
    start_date: date | None = None,
    end_date: date | None = None,
):
    items, total = repository.list(page, page_size, start_date, end_date)
    return FinancialList(
        items=items,
        meta=PaginationMeta(page=page, page_size=page_size, total=total),
    )


@router.get("/{financial_id}", response_model=FinancialResponse)
def get_financial(
    financial_id: str,
    repository: Annotated[FinancialRepository, Depends(get_financial_repository)],
):
    item = repository.get(financial_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Registro financeiro não encontrado.")
    return item


@router.patch("/{financial_id}", response_model=FinancialResponse)
def update_financial(
    financial_id: str,
    data: FinancialUpdate,
    repository: Annotated[FinancialRepository, Depends(get_financial_repository)],
    _: Annotated[dict, Depends(get_current_user)],
):
    item = repository.update(financial_id, data.model_dump(exclude_unset=True))
    if item is None:
        raise HTTPException(status_code=404, detail="Registro financeiro não encontrado.")
    return item


@router.delete("/{financial_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_financial(
    financial_id: str,
    repository: Annotated[FinancialRepository, Depends(get_financial_repository)],
    _: Annotated[dict, Depends(get_current_user)],
):
    if repository.delete(financial_id) is None:
        raise HTTPException(status_code=404, detail="Registro financeiro não encontrado.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
