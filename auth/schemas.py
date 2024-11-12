from pydantic import BaseModel, EmailStr, ConfigDict, validator
from datetime import datetime
from typing import Optional


class UserSchema(BaseModel):
    model_config = ConfigDict(strict=True, from_attributes=True)
    # id: int
    username: str
    password: str | bytes
    email: Optional[EmailStr] = None
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
    
    @validator('email', pre=True, always=True)
    def check_email(cls, v):
        if v in [None, '', 'null']:
            return None
        return v