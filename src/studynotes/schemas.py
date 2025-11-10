from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from pydantic import ConfigDict

# Общая ошибка
class APIError(BaseModel):
    code: str
    message: str
    details: dict | None = None

# User
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

class UserOut(BaseModel):
    id: int
    email: EmailStr
    role: str
    model_config = ConfigDict(from_attributes=True)

# Auth
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class LoginIn(BaseModel):
    email: EmailStr
    password: str

# Tag
class TagCreate(BaseModel):
    name: str

class TagOut(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)

# Note
class NoteBase(BaseModel):
    title: str
    body: str

class NoteCreate(NoteBase):
    tags: List[str] | None = None

class NotePatch(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    tags: Optional[List[str]] = None

class NoteOut(NoteBase):
    id: int
    owner_id: int
    tags: list[str] = []
    model_config = ConfigDict(from_attributes=True)
