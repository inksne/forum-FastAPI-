from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.security import HTTPBearer
from fastapi.responses import RedirectResponse
from auth.helpers import create_access_token, create_refresh_token
from auth.validation import (
    get_current_token_payload,
    get_current_auth_user_for_refresh,
    get_current_active_auth_user,
    validate_auth_user_db
)
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from database.database import get_async_session
from models.models import User
from datetime import timedelta

http_bearer = HTTPBearer(auto_error=False)

class TokenInfo(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "Bearer"


router = APIRouter(prefix='/jwt', tags=["JWT"], dependencies=[Depends(http_bearer)])


@router.post('/login/', response_model=TokenInfo)
async def auth_user_issue_jwt(response: Response, user: User = Depends(validate_auth_user_db)):
    access_token = create_access_token(user)
    refresh_token = create_refresh_token(user)
    
    # Сохраняем access_token в куки
    response.set_cookie(key="access_token", value=access_token, httponly=True, secure=False, max_age=timedelta(hours=2))
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, secure=False, max_age=timedelta(days=30))  # опционально
    
    return TokenInfo(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh/", response_model=TokenInfo, response_model_exclude_none=True)
async def auth_refresh_jwt(user: User = Depends(get_current_auth_user_for_refresh)):
    access_token = create_access_token(user)
    return TokenInfo(access_token=access_token)


@router.get('/users/me/')
async def auth_user_check_self_info(
    payload: dict = Depends(get_current_token_payload), 
    user: User = Depends(get_current_active_auth_user),
):
    iat = payload.get("iat")
    return {
        "username": user.username,
        "email": user.email,
        "logged_in_at": iat,
    }

@router.post('/logout')
async def logout(response: Response):
    """Удаляем токен из куки и перенаправляем на главную страницу."""
    
    # Удаляем куки, установив максимальное время жизни в прошлом
    response.delete_cookie(key="access_token", httponly=True, secure=False, samesite="Lax")
    response.delete_cookie(key="refresh_token", httponly=True, secure=False, samesite="Lax")

    # Перенаправляем на главную страницу
    # return RedirectResponse(url="/")