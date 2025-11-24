from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.api.deps.current_user import get_current_user
from app.models.user import User
from app.models.api_key import ApiKey
from app.schemas.api_key import ApiKeyCreate, ApiKeyResponse
from app.services.api_key import ApiKeyService
from app.repositories.api_key import ApiKeyRepository

router = APIRouter()

async def get_api_key_service(session: AsyncSession = Depends(get_session)) -> ApiKeyService:
    return ApiKeyService(ApiKeyRepository(model=ApiKey, db_session=session))

@router.post("", response_model=ApiKeyResponse)
async def create_api_key(
    data: ApiKeyCreate,
    current_user: User = Depends(get_current_user),
    service: ApiKeyService = Depends(get_api_key_service),
):
    """
    创建 API Key

    返回的 plaintext_key 是明文,只在创建时显示一次,请妥善保管
    """
    api_key = await service.create_api_key(current_user.uuid, data)
    return ApiKeyResponse.from_orm_with_plaintext(api_key)

@router.get("", response_model=list[ApiKeyResponse])
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    service: ApiKeyService = Depends(get_api_key_service),
):
    """
    获取当前用户的所有 API Keys

    返回的 plaintext_key 是解密后的明文
    """
    api_keys = await service.get_user_api_keys(current_user.uuid)
    return [ApiKeyResponse.from_orm_with_plaintext(key) for key in api_keys]

@router.delete("/{encrypted_key}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    encrypted_key: str,
    current_user: User = Depends(get_current_user),
    service: ApiKeyService = Depends(get_api_key_service),
):
    """
    删除 API Key

    Args:
        encrypted_key: 加密后的 key (从列表接口获取)
    """
    success = await service.revoke_api_key(current_user.uuid, encrypted_key)
    if not success:
        raise HTTPException(status_code=404, detail="API Key not found")
