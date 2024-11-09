from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter()

templates = Jinja2Templates(directory='templates')

@router.get('/')
def get_base_page(request: Request):
    return templates.TemplateResponse('index.html', {'request': request})

@router.get('/jwt/login/')
def get_login_page(request: Request):
    return templates.TemplateResponse('login.html', {'request': request})

@router.get('/register')
def get_register_page(request: Request):
    return templates.TemplateResponse('register.html', {'request': request})

@router.get('/authenticated/')
def get_authenticated_page(request: Request):
    return templates.TemplateResponse('authenticated.html', {'request': request})