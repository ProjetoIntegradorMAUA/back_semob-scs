from typing import Annotated

from fastapi import APIRouter, Depends

from src.app.api.dependencies import (
    get_current_user,
    get_preference_repository,
)
from src.app.repositories.preference_repository import PreferenceRepository
from src.app.schemas.preference import PreferenceResponse, PreferenceUpdate

router = APIRouter(prefix="/preferences", tags=["Preferências"])


@router.get("/me", response_model=PreferenceResponse)
def get_my_preferences(
    user: Annotated[dict, Depends(get_current_user)],
    repository: Annotated[PreferenceRepository, Depends(get_preference_repository)],
):
    existing = repository.get_by_user(user["id"])
    if existing:
        return existing
    return repository.upsert(user["id"], PreferenceUpdate().model_dump())


@router.put("/me", response_model=PreferenceResponse)
def update_my_preferences(
    data: PreferenceUpdate,
    user: Annotated[dict, Depends(get_current_user)],
    repository: Annotated[PreferenceRepository, Depends(get_preference_repository)],
):
    return repository.upsert(user["id"], data.model_dump())
