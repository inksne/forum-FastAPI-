from fastapi import FastAPI, Depends, HTTPException, APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel
from datetime import datetime

from database.database import create_db_and_tables, get_async_session
from models.models import Role, Post, User
from auth.auth import router as jwt_router


app = FastAPI(
    title='forum'
)


#CORS
origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost:3000",
    "http://localhost:8080",
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],
)

#pydantic модели для restfulAPI
class PostCreate(BaseModel):
    author_id: int
    title: str
    description: str

class RoleResponse(BaseModel):
    id: int
    name: str
    permissions: dict

class PostResponse(BaseModel):
    id: int
    deployed_at: datetime
    author_id: int
    description: str

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    password: str
    registered_at: datetime
    role_id: int

class UserUpdateUsername(BaseModel):
    username: str

#restfulAPI

@app.on_event("startup")
async def startup():
    await create_db_and_tables()



@app.post("/roles/", response_model=dict)
async def create_role(name: str, permissions: dict = None, session: AsyncSession = Depends(get_async_session)):
    new_role = Role(name=name, permissions=permissions)
    session.add(new_role)
    await session.commit()
    await session.refresh(new_role)  # Обновить объект, чтобы получить id
    return {"id": new_role.id, "name": new_role.name, "permissions": new_role.permissions}



@app.get("/roles/", response_model=list[dict])
async def get_all_roles(session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(select(Role))
    roles = result.scalars().all()
    return [{"id": role.id, "name": role.name, "permissions": role.permissions} for role in roles]



@app.get('/posts/', response_model=list[dict])
async def get_all_posts(session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(select(Post))
    posts = result.scalars().all()
    return [{'id': post.id, 'deployed_at': post.deployed_at, 'author_id': post.author_id, 'description': post.description} for post in posts]



@app.post('/posts/', response_model=PostResponse)
async def create_post(post: PostCreate, session: AsyncSession = Depends(get_async_session)):
    new_post = Post(author_id=post.author_id, title=post.title, description=post.description)
    session.add(new_post)
    await session.commit()
    await session.refresh(new_post)
    return new_post



@app.get('/users/{user_id}', response_model=UserResponse)
async def get_user_by_id(user_id: int, session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail='Пользователь не найден')
    return user



@app.get('/users/', response_model=list[dict])
async def get_all_users(session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(select(User))
    users = result.scalars().all()
    return [
        {'id': user.id,
        'email': user.email,
        'username': user.username,
        'registered_at': user.registered_at,
        'role_id': user.role_id} 
        for user in users]



@app.put('/users/{user_id}', response_model=UserResponse)
async def change_username(user_id: int, user_update_username: UserUpdateUsername, session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail='Пользователь не найден')
    user.username = user_update_username.username
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user



@app.get('/roles/{role_id}', response_model=RoleResponse)
async def get_role_by_id(role_id: int, session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(select(Role).where(Role.id == role_id))
    role = result.scalar_one_or_none()
    if role is None:
        raise HTTPException(status_code=404, detail='Роль не найдена')
    return role



@app.delete('/users/{user_id}', response_model=str)
async def delete_user_by_id(user_id: int, user_password: str, session: AsyncSession = Depends(get_async_session)):

    result_user = await session.execute(select(User).where(User.id == user_id, User.hashed_password == user_password))
    user = result_user.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(status_code=404, detail='Пользователь не найден')

    result_posts = await session.execute(select(Post).where(Post.author_id == user_id))
    posts = result_posts.scalars().all()

    for post in posts:
        await session.delete(post)

    await session.delete(user)
    await session.commit()
    
    return 'Пользователь и все его посты успешно удалены.'

#роутеры

app.include_router(jwt_router)