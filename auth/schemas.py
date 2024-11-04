from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime


class UserSchema(BaseModel):
    model_config = ConfigDict(strict=True)
    # id: int
    username: str
    password: bytes
    email: EmailStr | None = None
    # registered_at: datetime
    # role_id: int
    active: bool = True