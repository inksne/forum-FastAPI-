from fastapi import Depends, HTTPException, Form
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError
from starlette import status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from auth.helpers import TOKEN_TYPE_FIELD, ACCESS_TOKEN_TYPE, REFRESH_TOKEN_TYPE
from auth.utils import decode_jwt, validate_password
from auth.schemas import UserSchema
from models.models import User
from database.database import get_async_session


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/jwt/login")


def get_current_token_payload(
    token: str = Depends(oauth2_scheme)
) -> dict:
    try:
        payload = decode_jwt(token=token)
    except InvalidTokenError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'Invalid token error: {e}')
    return payload


def validate_token_type(payload: dict, token_type: str) -> bool:
    current_token_type = payload.get(TOKEN_TYPE_FIELD)
    if current_token_type == token_type:
        return True
    raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token type {current_token_type!r} expected {token_type!r}"
        )


def get_current_auth_user_from_token_of_type(token_type: str):
    async def get_auth_user_from_token(payload: dict = Depends(get_current_token_payload), db: AsyncSession = Depends(get_async_session)) -> User:
        validate_token_type(payload, token_type)
        return await get_user_by_token_sub(payload, db)
    return get_auth_user_from_token



get_current_auth_user = get_current_auth_user_from_token_of_type(ACCESS_TOKEN_TYPE)

get_current_auth_user_for_refresh = get_current_auth_user_from_token_of_type(REFRESH_TOKEN_TYPE)

async def get_user_by_token_sub(payload: dict, db: AsyncSession) -> User:
    username: str | None = payload.get("sub")
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalars().first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalid (user not found)")

    return user

async def get_current_active_auth_user(user: User = Depends(get_current_auth_user)):
    if user.active:
        return user
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='User inactive')


async def validate_auth_user_db(username: str = Form(...), password: str = Form(...), db: AsyncSession = Depends(get_async_session)):
    unauthed_exc = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    
    user = await db.execute(select(User).where(User.username == username))
    user = user.scalars().first()  

    if not user:
        raise unauthed_exc
    
    if not validate_password(password=password, hashed_password=user.password.encode('utf-8')):
        raise unauthed_exc

    if not user.active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User inactive")
    
    return UserSchema.from_attributes(user)


# def get_current_auth_user_for_refresh(payload: dict = Depends(get_current_token_payload)) -> UserSchema:
#     validate_token_type(payload, REFRESH_TOKEN_TYPE)
#     return get_user_by_token_sub(payload)