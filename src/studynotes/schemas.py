from pydantic import BaseModel, ConfigDict, EmailStr, Field


class APIError(BaseModel):
    code: str
    message: str
    details: dict | None = None


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserOut(BaseModel):
    id: int
    email: EmailStr
    role: str
    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TagCreate(BaseModel):
    name: str


class TagOut(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)


class NoteBase(BaseModel):
    title: str
    body: str


class NoteCreate(NoteBase):
    tags: list[str] | None = None


class NotePatch(BaseModel):
    title: str | None = None
    body: str | None = None
    tags: list[str] | None = None


class NoteOut(NoteBase):
    id: int
    owner_id: int
    tags: list[str] = []
    model_config = ConfigDict(from_attributes=True)
