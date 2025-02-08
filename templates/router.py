from fastapi import APIRouter, Request, Depends, HTTPException, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
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

templates.env.filters['truncatewords'] = truncate_words

class PostCreate(BaseModel):
    title: str
    description: str

@router.get('/')
def get_base_page(request: Request):
    return templates.TemplateResponse(request, 'index.html')



@router.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    post = {
        'description': "Это очень длинное описание, которое должно быть обрезано после определенного количества слов."
    }
    return templates.TemplateResponse(request, "posts.html", {"post": post})



@router.get('/jwt/login/')
def get_login_page(request: Request):
    return templates.TemplateResponse(request, 'login.html')



@router.get('/register')
def get_register_page(request: Request):
    return templates.TemplateResponse(request, 'register.html')



@router.get('/about_us')
def get_about_us_page(request: Request):
    return templates.TemplateResponse(request, 'about_us.html')



@router.get('/authenticated/users/{user_id}/edit/')
async def edit_profile_page(
    request: Request,
    user_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_auth_user)
):
    if current_user.role_id == 6:
        return templates.TemplateResponse(request, '403.html')

    if current_user.id != user_id and current_user.role_id != 3 and current_user.role_id != 4:
        return templates.TemplateResponse(request, '403.html')

    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        return templates.TemplateResponse(request, '404.html')

    return templates.TemplateResponse(request, 'edit_profile.html', {'user': user, 'current_user': current_user})




@router.get('/authenticated/posts/')
async def get_all_posts(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_auth_user)
):
    if current_user.role_id == 6:
        return templates.TemplateResponse(request, '403.html')
    result = await session.execute(select(Post).options(selectinload(Post.author)))
    posts = result.scalars().all()
    return templates.TemplateResponse(request, 'posts.html', {'posts': posts, 'current_user': current_user})



@router.get('/authenticated/posts/{post_id}/comments_create/')
async def get_comment_create_page(
    request: Request,
    post_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_auth_user)
):
    if current_user.role_id == 6:
        return templates.TemplateResponse(request, '403.html')
    result_post = await session.execute(select(Post).where(Post.id == post_id))
    post = result_post.scalar_one_or_none()
    if not post:
        return templates.TemplateResponse(request, '404.html')
    return templates.TemplateResponse(request, 'comments_create.html', {'post': post, 'current_user': current_user})



@router.get('/authenticated/posts/{post_id}/comments')
async def get_comments_for_post(
    request: Request,
    post_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_auth_user)
):
    if current_user.role_id == 6:
        return templates.TemplateResponse(request, '403.html')
    result_post = await session.execute(
        select(Post)
        .where(Post.id == post_id)
        .options(selectinload(Post.comments).selectinload(Comment.author))
    )
    post = result_post.scalar_one_or_none()
    if not post:
        return templates.TemplateResponse(request, '404.html')
    comments = post.comments
    return templates.TemplateResponse(
        request, "comments.html", {
            "post": post,
            "comments": comments,
            'current_user': current_user
        })



@router.post('/authenticated/posts/{post_id}/comments/create')
async def create_comment(
    request: Request,
    post_id: int,
    content: str = Form(...),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_auth_user)
):
    if current_user.role_id == 6:
        return templates.TemplateResponse(request, '403.html')
    result_post = await session.execute(select(Post).where(Post.id == post_id))
    post = result_post.scalar_one_or_none()
    if not post:
        return templates.TemplateResponse(request, '404.html')
    if not content.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Контент комментария не может быть пустым') 
    new_comment = Comment(post_id=post.id, author_id=current_user.id, content=content)
    session.add(new_comment)
    await session.commit()
    await session.refresh(new_comment)
    return templates.TemplateResponse(
        request, "comments_create.html", {
            "post": post,
            "comment": new_comment,
            'current_user': current_user
        })


@router.get('/authenticated/posts/create')
async def create_post_page(request: Request, current_user: User = Depends(get_current_active_auth_user)):
    if current_user.role_id == 6:
        return templates.TemplateResponse(request, '403.html')
    return templates.TemplateResponse(request, 'create_post.html', {'current_user': current_user})



@router.post('/authenticated/posts/create_post/')
async def create_post(
    post: PostCreate,
    current_user: User = Depends(get_current_active_auth_user),
    session: AsyncSession = Depends(get_async_session)
):
    if current_user.role_id == 6:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Вы забанены')
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
    if current_user.role_id in {1, 6} and current_user.id != post.author_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав для удаления поста")
    if not post:
        raise HTTPException(status_code=404, detail="Пост не найден")
    for comment in post.comments:
        await session.delete(comment)
    await session.delete(post)
    await session.commit()
    return 'Пост удален'


@router.get('/authenticated/users/{user_id}/')
async def get_user_profile_page(
    request: Request,
    user_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_auth_user)
):
    if current_user.role_id == 6:
        return templates.TemplateResponse(request, '403.html')
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        return templates.TemplateResponse(request, '404.html')

    return templates.TemplateResponse(request, 'profile.html', {'user': user, 'current_user': current_user})



@router.post('/authenticated/users/{user_id}/edit')
async def update_profile(
    user_id: int,
    username: str = Form(...),  
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_auth_user)
):
    if current_user.role_id == 6:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Вы забанены')

    if current_user.id != user_id and current_user.role_id not in {3, 4}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав для редактирования")

    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

    user.username = username
    session.add(user)
    await session.commit()
    await session.refresh(user)

    return RedirectResponse(url=f"/authenticated/users/{user.id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post('/authenticated/users/{user_id}/delete')
async def delete_user(
    request: Request,
    user_id: int,
    current_user: User = Depends(get_current_active_auth_user),
    session: AsyncSession = Depends(get_async_session)
):
    if current_user.id != user_id and current_user.role_id not in {3, 4}:
        return templates.TemplateResponse(request, '403.html')

    result = await session.execute(select(User).where(User.id == user_id))
    user_to_delete = result.scalar_one_or_none()
    if not user_to_delete:
        return templates.TemplateResponse(request, '404.html')

    result_posts = await session.execute(select(Post).where(Post.author_id == user_id))
    posts = result_posts.scalars().all()
    for post in posts:
        await session.delete(post)

    result_comments = await session.execute(select(Comment).where(Comment.author_id == user_id))
    comments = result_comments.scalars().all()
    for comment in comments:
        await session.delete(comment)

    await session.delete(user_to_delete)
    await session.commit()

    return templates.TemplateResponse(request, '404.html')



@router.post('/authenticated/users/{user_id}/ban')
async def ban_user(
    user_id: int, 
    current_user: User = Depends(get_current_active_auth_user),
    session: AsyncSession = Depends(get_async_session)
):
    if current_user.role_id not in {3, 4}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")

    result = await session.execute(select(User).where(User.id == user_id))
    user_to_ban = result.scalar_one_or_none()
    if not user_to_ban:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

    user_to_ban.role_id = 6
    session.add(user_to_ban)
    await session.commit()
    await session.refresh(user_to_ban)

    return {'detail': 'Пользователь заблокирован'}



@router.post('/authenticated/users/{user_id}/unban')
async def unban_user(
    user_id: int, 
    current_user: User = Depends(get_current_active_auth_user),
    session: AsyncSession = Depends(get_async_session)
):
    if current_user.role_id not in {3, 4}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")

    result = await session.execute(select(User).where(User.id == user_id))
    user_to_unban = result.scalar_one_or_none()
    if not user_to_unban:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

    user_to_unban.role_id = 1
    session.add(user_to_unban)
    await session.commit()
    await session.refresh(user_to_unban)

    return {'detail': 'Пользователь разблокирован'}