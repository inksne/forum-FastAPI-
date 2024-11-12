from fastapi import APIRouter, Request, Depends, HTTPException, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from starlette import status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from models.models import User, Post, Comment
from database.database import get_async_session
from auth.validation import get_current_active_auth_user
from pydantic import BaseModel


router = APIRouter()


templates = Jinja2Templates(directory='templates')


def truncate_words(value, num_words):
    words = value.split()
    if len(words) > num_words:
        return ' '.join(words[:num_words]) + '...'
    return value

# Добавление фильтра в Jinja2 Environment
templates.env.filters['truncatewords'] = truncate_words

class PostCreate(BaseModel):
    title: str
    description: str


@router.get('/')
def get_base_page(request: Request):
    return templates.TemplateResponse('index.html', {'request': request})


@router.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    post = {
        'description': "Это очень длинное описание, которое должно быть обрезано после определенного количества слов."
    }
    return templates.TemplateResponse("posts.html", {"request": request, "post": post})


@router.get('/jwt/login/')
def get_login_page(request: Request):
    return templates.TemplateResponse('login.html', {'request': request})



@router.get('/register')
def get_register_page(request: Request):
    return templates.TemplateResponse('register.html', {'request': request})



@router.get('/authenticated/')
def get_authenticated_page(request: Request):
    return templates.TemplateResponse('authenticated.html', {'request': request})



@router.get('/authenticated/posts/')
async def get_all_posts(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_auth_user)
):
    result = await session.execute(select(Post).options(selectinload(Post.author)))
    posts = result.scalars().all()
    return templates.TemplateResponse('posts.html', {'request': request, 'posts': posts})



@router.get('/authenticated/posts/{post_id}/comments_create/')
async def get_comment_create_page(
    request: Request,
    post_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_auth_user)
):
    result_post = await session.execute(select(Post).where(Post.id == post_id))
    post = result_post.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Пост не найден")
    return templates.TemplateResponse('comments_create.html', {'request': request, 'post': post})



@router.get('/authenticated/posts/{post_id}/comments')
async def get_comments_for_post(
    request: Request,
    post_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_auth_user)
):
    result_post = await session.execute(
        select(Post)
        .where(Post.id == post_id)
        .options(selectinload(Post.comments).selectinload(Comment.author))
    )
    post = result_post.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Пост не найден")
    comments = post.comments
    return templates.TemplateResponse("comments.html", {"request": request, "post": post, "comments": comments})



@router.post('/authenticated/posts/{post_id}/comments/create')
async def create_comment(
    request: Request,
    post_id: int,
    content: str = Form(...),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_auth_user)
):
    result_post = await session.execute(select(Post).where(Post.id == post_id))
    post = result_post.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Пост не найден")
    if not content.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Контент комментария не может быть пустым') 
    new_comment = Comment(post_id=post.id, author_id=current_user.id, content=content)
    session.add(new_comment)
    await session.commit()
    await session.refresh(new_comment)
    return templates.TemplateResponse("comments_create.html", {"request": request, "post": post, "comment": new_comment})


@router.get('/authenticated/posts/create')
async def create_post_page(request: Request):
    return templates.TemplateResponse('create_post.html', {'request': request})



@router.post('/authenticated/posts/create_post/')
async def create_post(
    post: PostCreate,
    current_user: User = Depends(get_current_active_auth_user),
    session: AsyncSession = Depends(get_async_session)
):
    new_post = Post(
        author_id=current_user.id, 
        title=post.title, 
        description=post.description
    )
    session.add(new_post)
    await session.commit()
    await session.refresh(new_post)
    return new_post 

@router.delete('/authenticated/posts/{post_id}')
async def delete_post(
    post_id: int,
    current_user: User = Depends(get_current_active_auth_user),
    session: AsyncSession = Depends(get_async_session)
):
    result_post = await session.execute(select(Post).where(Post.id == post_id).options(selectinload(Post.comments)))
    post = result_post.scalar_one_or_none()
    if current_user.role_id == 1 and current_user.id != post.author_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав для удаления поста")
    if not post:
        raise HTTPException(status_code=404, detail="Пост не найден")
    for comment in post.comments:
        await session.delete(comment)
    await session.delete(post)
    await session.commit()
    return 'Пост удален'