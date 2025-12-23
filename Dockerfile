# syntax=docker/dockerfile:1.7-labs

FROM python:3.12-slim AS build

ENV PIP_DISABLE_PIP_VERSION_CHECK=on \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml .
COPY src ./src

RUN --mount=type=cache,target=/root/.cache \
    python -m pip install --upgrade pip && \
    pip wheel --no-deps --wheel-dir=/wheels .

FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=on

WORKDIR /app

RUN groupadd -r app && useradd -r -g app app

COPY --from=build /wheels /wheels
RUN pip install --no-cache-dir /wheels/*

COPY src ./src
RUN chown -R app:app /app

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request,sys; \
  import socket; \
  socket.setdefaulttimeout(2); \
  \
  import urllib.error; \
  \
  try: urllib.request.urlopen('http://127.0.0.1:8000/healthz'); \
  except Exception: sys.exit(1); \
  sys.exit(0)"


CMD ["uvicorn", "studynotes.main:app", "--host", "0.0.0.0", "--port", "8000"]
