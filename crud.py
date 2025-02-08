from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, Depends
from models.models import User
from pydantic import BaseModel
from datetime import datetime

class UserCRUDResponse(BaseModel):
    id: int
    email: str
    username: str
    password: str
    registered_at: datetime
    role_id: int

async def get_user_by_username(user_username: str, session: AsyncSession) -> UserCRUDResponse:
    result = await session.execute(select(User).where(User.username == user_username))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail='Пользователь не найден')
    return user