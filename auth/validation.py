from fastapi import Depends, HTTPException, Form
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError
from starlette import status

from auth.helpers import TOKEN_TYPE_FIELD, ACCESS_TOKEN_TYPE, REFRESH_TOKEN_TYPE
from auth.utils import decode_jwt, validate_password, hash_password
from auth.schemas import UserSchema


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/jwt/login")


john = UserSchema(
    username="john",
    password=hash_password("qwerty"),
    email='john@example.com',
)


sam = UserSchema(
    username='sam',
    password=hash_password('secret')
)


users_db: dict[str, UserSchema] = {
    john.username: john,
    sam.username: sam,
}


def get_current_token_payload(
    token: str = Depends(oauth2_scheme)
) -> UserSchema:
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


def get_current_auth_user_from_token_of_type(token_type: str) -> UserSchema:
    def get_auth_user_from_token(payload: dict = Depends(get_current_token_payload)) -> UserSchema:
        validate_token_type(payload, token_type)
        return get_user_by_token_sub(payload)
    return get_auth_user_from_token


class UserGetterFromToken:
    def __init__(self, token_type: str):
        self.token_type = token_type

    def __call__(self, payload: dict = Depends(get_current_token_payload)):
        validate_token_type(payload, self.token_type)
        return get_user_by_token_sub(payload)

get_current_auth_user = UserGetterFromToken(ACCESS_TOKEN_TYPE)

get_current_auth_user_for_refresh = UserGetterFromToken(REFRESH_TOKEN_TYPE)

def get_user_by_token_sub(payload: dict) -> UserSchema:
    username: str | None = payload.get("sub")
    if user := users_db.get(username):
        return user
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalid (user not found)")


def get_current_active_auth_user(user: UserSchema = Depends(get_current_auth_user)):
    if user.active:
        return user
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='User inactive')


def validate_auth_user(username: str = Form(...), password: str = Form(...)):
    unauthed_exc = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    if not (user := users_db.get(username)):
        raise unauthed_exc
    if not validate_password(password=password, hashed_password=user.password):
        raise unauthed_exc
    if not user.active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User inactive")
    return user


# def get_current_auth_user_for_refresh(payload: dict = Depends(get_current_token_payload)) -> UserSchema:
#     validate_token_type(payload, REFRESH_TOKEN_TYPE)
#     return get_user_by_token_sub(payload)