import logging

from pydantic import BaseModel, EmailStr, Field, validator
from datetime import datetime, date
from typing import Optional

logger = logging.getLogger(__name__)

# Request Models
class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=60)

    @validator('password')
    def validate_password(cls, v):
        if not any(char.isdigit() for char in v):
            logger.info("비밀번호에는 숫자가 포함되어야 합니")
            raise ValueError('비밀번호에는 숫자가 포함되어야 합니다')
        if not any(char.isupper() for char in v):
            logger.info('비밀번호에는 대문자를 하나 이상 포함해야 합니다')
            raise ValueError('비밀번호에는 대문자를 하나 이상 포함해야 합니다')
        return v

class UserLoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_info: "UserInfoResponse"

class UserInfoResponse(BaseModel):
    #account
    account_id: int
    username: str
    email: str
    role: str
    is_active: bool

    #user_profile
    user_id: int
    name: str
    phone_number: Optional[str]
    date_of_birth: Optional[date]
    gender: Optional[str]
    address: Optional[str]

    created_at: datetime

    class Config:
        from_attributes = True

class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=8)

class UserUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    phone_number: Optional[str] = Field(None, max_length=20)
    date_of_birth: Optional[date] = None
    gender: Optional[str] = Field(None, max_length=10)
    address: Optional[str] = Field(None, max_length=255)