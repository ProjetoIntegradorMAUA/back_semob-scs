from typing import Annotated

from fastapi import APIRouter, Depends

from src.app.api.dependencies import (
    get_current_user,
    get_preference_repository,
)
from src.app.repositories.preference_repository import PreferenceRepository
from src.app.schemas.preference import (
    PreferenceResponse,
    PreferenceSettings,
    PreferenceUpdate,
)

router = APIRouter(prefix="/preferences", tags=["Preferências"])


@router.get("/me", response_model=PreferenceResponse)
def get_my_preferences(
    user: Annotated[dict, Depends(get_current_user)],
    repository: Annotated[PreferenceRepository, Depends(get_preference_repository)],
):
    existing = repository.get_by_user(user["id"])
    if existing:
        return existing
    return repository.upsert(user["id"], PreferenceSettings().model_dump())


@router.put("/me", response_model=PreferenceResponse)
@router.patch("/me", response_model=PreferenceResponse)
def update_my_preferences(
    data: PreferenceUpdate,
    user: Annotated[dict, Depends(get_current_user)],
    repository: Annotated[PreferenceRepository, Depends(get_preference_repository)],
):
    changes = data.model_dump(exclude_unset=True, exclude_none=True)
    if repository.get_by_user(user["id"]) is None:
        changes = {**PreferenceSettings().model_dump(), **changes}
    return repository.upsert(user["id"], changes)
