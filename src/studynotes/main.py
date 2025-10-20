from fastapi import FastAPI
from pydantic import BaseModel, constr
from starlette.exceptions import HTTPException as StarletteHTTPException

from .errors import make_exception_handlers

app = FastAPI(
    title="Study Notes API",
    version="0.1.0",
    exception_handlers=make_exception_handlers(),  # RFC7807 хендлеры
)


@app.get("/health")
def health():
    return {"status": "ok"}


class ValidateIn(BaseModel):
    name: constr(min_length=1)


@app.post("/validate")
def validate_payload(payload: ValidateIn):
    return {"ok": True}


@app.get("/__nope__")
def force_404():
    raise StarletteHTTPException(status_code=404, detail="Not Found")


# catch-all: чтобы неизвестные пути тоже проходили через наш хендлер
@app.api_route(
    "/{_path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
)
def catch_all(_path: str):
    raise StarletteHTTPException(status_code=404, detail="Not Found")
