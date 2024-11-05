from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime


class UserSchema(BaseModel):
    model_config = ConfigDict(strict=True, from_attributes=True)
    # id: int
    username: str
    password: str | bytes
    email: EmailStr | None = None
    # registered_at: datetime
    # role_id: int
    active: bool = True

    @classmethod
    def from_attributes(cls, obj):
        return cls(
            username=obj.username,
            password=obj.password,
            email=obj.email,
            active=obj.active
        )