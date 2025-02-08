from fastapi import FastAPI, Depends, HTTPException, APIRouter, Form
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from starlette import status

from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from database.database import create_db_and_tables, get_async_session
from models.models import Role, Post, User, Comment
from auth.auth import router as jwt_router
from auth.utils import hash_password
from auth.validation import get_current_active_auth_user
from templates.router import router as base_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)


#CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],
)

#pydantic модели для restfulAPI
class RoleResponse(BaseModel):
    id: int
    name: str
    permissions: dict

class UserResponse(BaseModel):
    id: int
    email: Optional[str] = None
    username: str
    registered_at: datetime
    role_id: int

class UserUpdateUsername(BaseModel):
    username: str

class UserCreate(BaseModel):
    username: str
    email: Optional[str] = None
    password: str

class CommentCreate(BaseModel):
    author_id: int
    post_id: int
    content: str

#restfulAPI

#роли

@app.post("/authenticated/roles/", response_model=dict)
async def create_role(
    name: str,
    permissions: dict = None,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_auth_user)
):
    if current_user.role_id != 4:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Недостаточно прав')
    new_role = Role(name=name, permissions=permissions)
    session.add(new_role)
    await session.commit()
    await session.refresh(new_role)  
    return {"id": new_role.id, "name": new_role.name, "permissions": new_role.permissions}



@app.get("/authenticated/roles/", response_model=list[dict])
async def get_all_roles(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_auth_user)
):
    if current_user.role_id == 6:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Вы забанены')
    result = await session.execute(select(Role))
    roles = result.scalars().all()
    return [{"id": role.id, "name": role.name, "permissions": role.permissions} for role in roles]



@app.get('/authenticated/roles/{role_id}', response_model=RoleResponse)
async def get_role_by_id(
    role_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_auth_user)
):
    if current_user.role_id == 6:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Вы забанены')
    result = await session.execute(select(Role).where(Role.id == role_id))
    role = result.scalar_one_or_none()
    if role is None:
        raise HTTPException(status_code=404, detail='Роль не найдена')
    return role

#пользователи

@app.post('/register', response_model=UserResponse)
async def register(
    username: str = Form(...),
    password: str = Form(...),
    email: Optional[str] = Form(None),
    session: AsyncSession = Depends(get_async_session)
):
    if email in [None, '', 'null']:
        email = None
    hashed_password = hash_password(password).decode('utf-8')
    new_user = User(username=username, password=hashed_password, email=email)
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    return new_user



@app.get('/authenticated/users/', response_model=list[dict])
async def get_all_users(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_auth_user)
):
    if current_user.role_id == 6:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Вы забанены')
    result = await session.execute(select(User))
    users = result.scalars().all()
    return [
        {'id': user.id,
        'email': user.email,
        'username': user.username,
        'registered_at': user.registered_at,
        'role_id': user.role_id} 
        for user in users]



@app.put('/authenticated/users/role/{user_id}', response_model=UserResponse)
async def change_role(
    user_id: int,
    user_update_role: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_auth_user)
):
    if current_user.role_id != 4:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Недостаточно прав')
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail='Пользователь не найден')
    user.role_id = user_update_role
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user

#комментарии

@app.delete('/authenticated/posts/{post_id}/comments/{comment_id}')
async def delete_comment(
    post_id: int,
    comment_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_auth_user)
):
    if current_user.role_id == 6:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Вы забанены')
    result_post = await session.execute(select(Post).where(Post.id == post_id))
    post = result_post.scalar_one_or_none()
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Пост не найден')
    
    result_comment = await session.execute(select(Comment).where(Comment.id == comment_id))
    comment = result_comment.scalar_one_or_none()
    if current_user.role_id == 1 and current_user.id != comment.author_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Недостаточно прав')
    if comment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Комментарий не найден')
    
    await session.delete(comment)
    await session.commit()

    return 'Комментарий удален'
    

#роутеры

router = APIRouter()

app.include_router(jwt_router)

app.include_router(base_router)

app.mount('/static', StaticFiles(directory='static'), name='static')