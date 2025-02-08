from dotenv import load_dotenv
import os
from pydantic import BaseModel
from pydantic_settings import BaseSettings
from pathlib import Path

load_dotenv()

POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB")


class AuthJWT(BaseModel):
    private_key_path: Path = Path("certs") / "jwt-private.pem"
    public_key_path: Path = Path("certs") / "jwt-public.pem"
    algorithm: str = "RS256"
    access_token_expire_minutes: int = 120
    refresh_token_expire_days: int = 30


class Settings(BaseSettings):
    auth_jwt: AuthJWT = AuthJWT()


settings = Settings()