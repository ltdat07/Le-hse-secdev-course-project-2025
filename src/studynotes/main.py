from __future__ import annotations

from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, Request, status, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException as StarletteHTTPException
from uuid import uuid4
from typing import Any
from .database import Base, engine, get_db
from .models import Note, NoteTag, Tag, User
from .schemas import (
    NoteCreate,
    NoteOut,
    NotePatch,
    TagCreate,
    TagOut,
    Token,
    UserCreate,
    UserOut,
)
from .security import (
    create_access_token,
    get_current_user,
    hash_password,
    require_admin,
    verify_password,
)

def _json_safe(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, (bytes, bytearray)):
        try:
            return value.decode("utf-8", errors="replace")
        except Exception:
            return repr(value)
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(v) for v in value]
    return str(value)

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Study Notes API",
    version="1.0.0",
    swagger_ui_parameters={"persistAuthorization": True},
)

Base.metadata.create_all(bind=engine)


# ---------------------------------------------------------------------------
# RFC7807 helpers / error handlers
# ---------------------------------------------------------------------------


def _problem(
    *,
    request: Request,
    status_code: int,
    title: str,
    detail: str,
    code: str,
    details: dict | None = None,
) -> dict:
    return {
        "type": "about:blank",
        "title": title,
        "status": status_code,
        "detail": detail,
        "instance": str(request.url),
        "correlation_id": str(uuid4()),
        "code": code,
        "message": title,
        "details": details or {},
    }


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if isinstance(exc.detail, dict):
        body = dict(exc.detail)
        body.setdefault("type", "about:blank")
        body.setdefault("title", body.get("message", body.get("code", "Error")))
        body.setdefault("status", exc.status_code)
        body.setdefault("detail", body.get("message", ""))
        body.setdefault("instance", str(request.url))
        body.setdefault("correlation_id", str(uuid4()))
        body.setdefault("details", body.get("details") or {})
    else:
        body = _problem(
            request=request,
            status_code=exc.status_code,
            title=str(exc.detail),
            detail=str(exc.detail),
            code="HTTP_ERROR",
        )

    return JSONResponse(
        status_code=exc.status_code,
        content=body,
        media_type="application/problem+json",
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    correlation_id = str(uuid4())

    raw_errors = exc.errors()
    safe_errors = _json_safe(raw_errors)
    safe_body = _json_safe(getattr(exc, "body", None))

    detail_msg = "Request validation failed"
    if isinstance(raw_errors, list) and raw_errors:
        first = raw_errors[0]
        msg = first.get("msg")
        if isinstance(msg, str) and msg:
            detail_msg = msg

    content = {
        "type": "about:blank",
        "title": "Unprocessable Entity",
        "status": status.HTTP_422_UNPROCESSABLE_ENTITY,
        "detail": detail_msg,
        "instance": str(request.url),
        "correlation_id": correlation_id,
        "code": "VALIDATION_ERROR",
        "message": "Request validation failed",
        "details": {
            "errors": safe_errors,
            "body": safe_body,
        },
    }

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=content,
        media_type="application/problem+json",
    )



# Эндпоинт для теста валидации
class ValidateIn(BaseModel):
    name: str = Field(min_length=1)


@app.post("/validate")
def validate_name(body: ValidateIn):
    return {"ok": True}


# ---------------------------------------------------------------------------
# Healthcheck
# ---------------------------------------------------------------------------


@app.get("/health")
def health():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------


@app.post("/api/v1/auth/register", response_model=UserOut)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    exists = db.query(User).filter(User.email == payload.email).first()
    if exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "EMAIL_TAKEN",
                "message": "Email already registered",
                "details": {},
            },
        )

    user = User(email=payload.email, hashed_password=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/api/v1/auth/login", response_model=Token)
def login(payload: UserCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "INVALID_CREDENTIALS",
                "message": "Incorrect email or password",
                "details": {},
            },
        )

    token = create_access_token(sub=user.email)
    return {"access_token": token, "token_type": "bearer"}


# ---------------------------------------------------------------------------
# Tags
# ---------------------------------------------------------------------------


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


@app.get("/api/v1/tags", response_model=List[TagOut])
def list_tags(
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    return db.query(Tag).order_by(Tag.name).limit(limit).offset(offset).all()


# ---------------------------------------------------------------------------
# Notes
# ---------------------------------------------------------------------------


def _ensure_tags(db: Session, names: Optional[list[str]]):
    if not names:
        return []
    tags: list[Tag] = []
    for raw in names:
        name = raw.strip()
        if not name:
            continue
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "NOT_FOUND",
                "message": "Note not found",
                "details": {},
            },
        )

    return NoteOut(
        id=note.id,
        title=note.title,
        body=note.body,
        owner_id=note.owner_id,
        tags=[nt.tag.name for nt in note.tags],
    )


@app.get("/api/v1/notes", response_model=List[NoteOut])
def list_notes(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    tag: Optional[str] = None,
    q: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    query = db.query(Note)

    if user.role != "admin":
        query = query.filter(Note.owner_id == user.id)

    if tag:
        query = query.join(NoteTag).join(Tag).filter(Tag.name == tag)

    if q:
        like = f"%{q}%"
        query = query.filter((Note.title.like(like)) | (Note.body.like(like)))

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
            )
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "NOT_FOUND",
                "message": "Note not found",
                "details": {},
            },
        )

    if body.title is not None:
        note.title = body.title
    if body.body is not None:
        note.body = body.body

    if body.tags is not None:
        for nt in list(note.tags):
            db.delete(nt)

        db.flush()

        new_names: list[str] = []
        if body.tags:
            for raw in body.tags:
                name = raw.strip()
                if name and name not in new_names:
                    new_names.append(name)

        for t in _ensure_tags(db, new_names):
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


@app.delete("/api/v1/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(note_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    note = db.get(Note, note_id)
    if not note or (note.owner_id != user.id and user.role != "admin"):
        raise HTTPException(
            status_code=404,
            detail={"code": "NOT_FOUND", "message": "Note not found", "details": {}},
        )
    db.delete(note)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)



@app.get("/api/v1/admin/users", response_model=list[UserOut])
def adm_list_users(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return db.query(User).all()



def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description="Study Notes API",
        routes=app.routes,
    )

    components = openapi_schema.get("components", {})
    security_schemes = components.get("securitySchemes", {})
    if "OAuth2PasswordBearer" in security_schemes:
        security_schemes["OAuth2PasswordBearer"] = {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi