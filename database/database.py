from typing import AsyncGenerator

# from fastapi import Depends
# from fastapi_users.db import SQLAlchemyBaseUserTable, SQLAlchemyUserDatabase
# from sqlalchemy import Integer, String, TIMESTAMP, ForeignKey, Column, func, Boolean, JSON
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
# from sqlalchemy.orm import DeclarativeBase
# from sqlalchemy.ext.declarative import DeclarativeMeta, declarative_base

from config import DB_HOST, DB_NAME, DB_PASS, DB_PORT, DB_USER
from models.models import Base

DATABASE_URL = f'postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
# Base: DeclarativeMeta = declarative_base()


# class Base(DeclarativeBase):
#     pass


# class Role(Base):
#     __tablename__ = 'role'
#     id = Column(Integer, primary_key=True)
#     name = Column(String, nullable=False)
#     permissions = Column(JSON)

# class User(SQLAlchemyBaseUserTable[int], Base):
#     __tablename__ = 'user'
#     id = Column(Integer, primary_key=True)
#     email = Column(String, nullable=False)
#     username = Column(String, nullable=False)
#     hashed_password: str = Column(String(length=1024), nullable=False)
#     registered_at = Column(TIMESTAMP, server_default=func.now())
#     role_id = Column(Integer, ForeignKey(role.c.id))
#     is_active: bool = Column(Boolean, default=True, nullable=False)
#     is_superuser: bool = Column(Boolean, default=False, nullable=False)
#     is_verified: bool = Column(Boolean, default=False, nullable=False)

# class Post(Base):
#     __tablename__ = 'post'
#     id = Column(Integer, primary_key=True)
#     deployed_at = Column(TIMESTAMP, server_default=func.now())
#     author = Column(String, ForeignKey(user.username))
#     description = Column(String(length=1024), nullable=False)

engine = create_async_engine(DATABASE_URL)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


# async def get_user_db(session: AsyncSession = Depends(get_async_session)):
#     yield SQLAlchemyUserDatabase(session, User)