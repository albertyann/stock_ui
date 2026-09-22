# Multi-stage image for the Stock Watchlist app: the Vue SPA is built with
# Node, then served by FastAPI itself as static files — one container serves
# both the UI and the API on port 9000.
#
# Build context is the ui/ root (see ui/.dockerignore):
#   docker build -f backend/Dockerfile -t stock-watchlist .
# Compose does this via `docker compose up --build`.

# --- Stage 1: build the Vue frontend ------------------------------------------
FROM node:20-alpine AS frontend-build

WORKDIR /frontend

# package files first so `npm ci` is cached while frontend source changes.
# Default registry is the npmmirror.com mirror (registry.npmjs.org is
# unreachable/throttled from some networks, e.g. mainland China).
# Override with: docker build --build-arg NPM_REGISTRY=https://registry.npmjs.org
ARG NPM_REGISTRY=https://registry.npmmirror.com
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --registry=${NPM_REGISTRY}

COPY frontend/ ./
RUN npm run build

# --- Stage 2: Python runtime ---------------------------------------------------
# Base is Debian/glibc (python:3.11-slim), deliberately NOT alpine:
# pandas / numpy / psycopg2-binary / asyncpg only publish manylinux wheels for
# cp311, so alpine would force slow and fragile source builds.
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dependencies first: this layer stays cached while app code changes.
# Paths are relative to the build context (ui/ root), hence backend/ prefix.
# Default index is the Aliyun PyPI mirror (pypi.org is very slow from some
# networks, e.g. mainland China). Override with:
#   docker build --build-arg PIP_INDEX_URL=https://pypi.org/simple
ARG PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/
COPY backend/requirements.txt ./
RUN pip install --index-url ${PIP_INDEX_URL} -r requirements.txt

# Non-root runtime user; /app is writable so the app can create runtime files.
RUN useradd --create-home --uid 1000 app \
    && chown app:app /app

# Application code only. tests/, .env, caches and uvicorn.log are excluded by
# ui/.dockerignore and are intentionally never copied (compose injects env).
COPY --chown=app:app backend/app ./app
COPY --chown=app:app backend/scripts ./scripts

# Built SPA at /app/static; app/main.py mounts it only when it exists.
COPY --from=frontend-build --chown=app:app /frontend/dist ./static

USER app

EXPOSE 9000

# websockets is intentionally removed from requirements.txt; wsproto is the
# WebSocket implementation. No --reload in containers (compose handles health).
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9000", "--ws", "wsproto"]
