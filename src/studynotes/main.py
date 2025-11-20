from typing import Any
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException as StarletteHTTPException

from .database import Base, engine, get_db
from .models import Note, NoteTag, Tag, User
from .schemas import (LoginIn, NoteCreate, NoteOut, NotePatch, TagCreate,
                      TagOut, Token, UserCreate, UserOut)
from .security import (create_access_token, get_current_user, hash_password,
                       require_admin, verify_password)

app = FastAPI(title="Study Notes API", version="1.0")

Base.metadata.create_all(bind=engine)


def _code_by_status(status: int) -> str:
    return {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        409: "CONFLICT",
        422: "VALIDATION_ERROR",
        500: "INTERNAL_SERVER_ERROR",
    }.get(status, "HTTP_ERROR")


def problem_json_ext(
    *,
    status: int,
    title: str,
    detail: str,
    instance: str,
    correlation_id: str,
    type_: str = "about:blank",
    code: str | None = None,
    message: str | None = None,
    details: dict[str, Any] | None = None,
) -> JSONResponse:
    body = {
        "type": type_,
        "title": title,
        "status": status,
        "detail": detail,
        "instance": instance,
        "correlation_id": correlation_id,
        "code": code or _code_by_status(status),
        "message": message or (detail or title),
        "details": details or {},
    }
    return JSONResponse(
        status_code=status,
        content=body,
        media_type="application/problem+json",
    )


@app.middleware("http")
async def attach_correlation_id(request: Request, call_next):
    request.state.correlation_id = str(uuid4())
    try:
        response = await call_next(request)
        return response
    except StarletteHTTPException as exc:
        cid = getattr(request.state, "correlation_id", str(uuid4()))
        title_map = {
            404: "Not Found",
            403: "Forbidden",
            401: "Unauthorized",
        }
        title = title_map.get(exc.status_code, "HTTP Error")
        detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        return problem_json_ext(
            status=exc.status_code,
            title=title,
            detail=detail,
            instance=str(request.url),
            correlation_id=cid,
            code=("HTTP_ERROR" if exc.status_code == 404 else None),
        )


@app.exception_handler(StarletteHTTPException)
async def starlette_http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
):
    cid = getattr(request.state, "correlation_id", str(uuid4()))
    title_map = {
        404: "Not Found",
        403: "Forbidden",
        401: "Unauthorized",
    }
    title = title_map.get(exc.status_code, "HTTP Error")
    detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    return problem_json_ext(
        status=exc.status_code,
        title=title,
        detail=detail,
        instance=str(request.url),
        correlation_id=cid,
        code=("HTTP_ERROR" if exc.status_code == 404 else None),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    cid = getattr(request.state, "correlation_id", str(uuid4()))
    return problem_json_ext(
        status=422,
        title="Unprocessable Entity",
        detail=exc.errors()[0]["msg"] if exc.errors() else "Validation failed",
        instance=str(request.url),
        correlation_id=cid,
        type_="https://datatracker.ietf.org/doc/html/rfc4918#section-11.2",
        code="VALIDATION_ERROR",
    )


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


class ValidateIn(BaseModel):
    name: str = Field(min_length=1)


@app.post("/validate")
def validate_endpoint(_body: ValidateIn):
    return JSONResponse(status_code=204, content=None)


@app.post("/api/v1/auth/register", response_model=UserOut)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    exists = db.query(User).filter(User.email == payload.email).first()
    if exists:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(email=payload.email, hashed_password=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/api/v1/auth/login", response_model=Token)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    token = create_access_token(sub=user.email)
    return {"access_token": token}


@app.post("/api/v1/tags", response_model=TagOut)
def create_tag(
    body: TagCreate,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    name = body.name.strip()
    tag = db.query(Tag).filter(Tag.name == name).first()
    if tag:
        return tag
    tag = Tag(name=name)
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag


@app.get("/api/v1/tags", response_model=list[TagOut])
def list_tags(
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    return db.query(Tag).order_by(Tag.name).limit(limit).offset(offset).all()


def _ensure_tags(db: Session, names: list[str] | None):
    if not names:
        return []
    tags: list[Tag] = []
    for raw in names:
        name = raw.strip()
        t = db.query(Tag).filter(Tag.name == name).first()
        if not t:
            t = Tag(name=name)
            db.add(t)
            db.flush()
        tags.append(t)
    return tags


@app.post("/api/v1/notes", response_model=NoteOut)
def create_note(
    body: NoteCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    note = Note(title=body.title, body=body.body, owner_id=user.id)
    db.add(note)
    db.flush()
    for t in _ensure_tags(db, body.tags):
        db.add(NoteTag(note_id=note.id, tag_id=t.id))
    db.commit()
    db.refresh(note)
    return NoteOut(
        id=note.id,
        title=note.title,
        body=note.body,
        owner_id=note.owner_id,
        tags=[nt.tag.name for nt in note.tags],
    )


@app.get("/api/v1/notes/{note_id}", response_model=NoteOut)
def get_note(
    note_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    note = db.get(Note, note_id)
    if not note or (note.owner_id != user.id and user.role != "admin"):
        raise HTTPException(status_code=404, detail="Note not found")
    return NoteOut(
        id=note.id,
        title=note.title,
        body=note.body,
        owner_id=note.owner_id,
        tags=[nt.tag.name for nt in note.tags],
    )


@app.get("/api/v1/notes", response_model=list[NoteOut])
def list_notes(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    tag: str | None = None,
    q: str | None = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    query = db.query(Note).filter(
        (Note.owner_id == user.id) | (user.role == "admin"),
    )
    if tag:
        query = query.join(NoteTag).join(Tag).filter(Tag.name == tag)
    if q:
        like = f"%{q}%"
        query = query.filter(
            (Note.title.like(like)) | (Note.body.like(like)),
        )
    items = query.order_by(Note.id.desc()).limit(limit).offset(offset).all()
    out: list[NoteOut] = []
    for n in items:
        out.append(
            NoteOut(
                id=n.id,
                title=n.title,
                body=n.body,
                owner_id=n.owner_id,
                tags=[nt.tag.name for nt in n.tags],
            ),
        )
    return out


@app.patch("/api/v1/notes/{note_id}", response_model=NoteOut)
def patch_note(
    note_id: int,
    body: NotePatch,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    note = db.get(Note, note_id)
    if not note or (note.owner_id != user.id and user.role != "admin"):
        raise HTTPException(status_code=404, detail="Note not found")
    if body.title is not None:
        note.title = body.title
    if body.body is not None:
        note.body = body.body
    if body.tags is not None:
        for nt in list(note.tags):
            db.delete(nt)
        for t in _ensure_tags(db, body.tags):
            db.add(NoteTag(note_id=note.id, tag_id=t.id))
    db.commit()
    db.refresh(note)
    return NoteOut(
        id=note.id,
        title=note.title,
        body=note.body,
        owner_id=note.owner_id,
        tags=[nt.tag.name for nt in note.tags],
    )


@app.delete("/api/v1/notes/{note_id}", status_code=204)
def delete_note(
    note_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    note = db.get(Note, note_id)
    if not note or (note.owner_id != user.id and user.role != "admin"):
        raise HTTPException(status_code=404, detail="Note not found")
    db.delete(note)
    db.commit()
    return JSONResponse(status_code=204, content=None)


@app.get("/api/v1/admin/users", response_model=list[UserOut])
def adm_list_users(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return db.query(User).all()
