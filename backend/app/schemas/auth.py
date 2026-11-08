from datetime import datetime
from typing import Optional

try:
    from pydantic import BaseModel, EmailStr, Field
except ImportError:
    from pydantic import BaseModel, Field  # type: ignore
    EmailStr = str  # type: ignore


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    role: str
    user_id: int
    email: str
    full_name: str


class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None
    user_id: Optional[int] = None


class UserLogin(BaseModel):
    email: str
    password: str


class UserRegister(BaseModel):
    email: str
    full_name: str
    password: str
    role: str = "Faculty"
    department_id: Optional[int] = None


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    department_id: Optional[int] = None
    is_active: bool
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True
