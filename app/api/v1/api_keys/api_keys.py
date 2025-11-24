from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.api.deps.current_user import get_current_user
from app.models.user import User
from app.schemas.api_key import ApiKeyCreate, ApiKeyResponse
from app.services.api_key import ApiKeyService
from app.repositories.api_key import ApiKeyRepository

router = APIRouter()

async def get_api_key_service(session: AsyncSession = Depends(get_session)) -> ApiKeyService:
    return ApiKeyService(ApiKeyRepository(session))

@router.post("", response_model=ApiKeyResponse)
async def create_api_key(
    data: ApiKeyCreate,
    current_user: User = Depends(get_current_user),
    service: ApiKeyService = Depends(get_api_key_service),
    session: AsyncSession = Depends(get_session),
):
    return await service.create_api_key(session, current_user.id, data)

@router.get("", response_model=list[ApiKeyResponse])
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    service: ApiKeyService = Depends(get_api_key_service),
    session: AsyncSession = Depends(get_session),
):
    return await service.get_user_api_keys(session, current_user.id)

@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    key_id: int,
    current_user: User = Depends(get_current_user),
    service: ApiKeyService = Depends(get_api_key_service),
    session: AsyncSession = Depends(get_session),
):
    success = await service.revoke_api_key(session, current_user.id, key_id)
    if not success:
        raise HTTPException(status_code=404, detail="API Key not found")
