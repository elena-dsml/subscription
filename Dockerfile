FROM python:3.13.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.9.27 /uv /bin/uv

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    WORKON_HOME=/opt/app/.venv \
    PATH=/opt/app/.venv/bin:$PATH

WORKDIR /opt/app

COPY pyproject.toml uv.lock alembic.ini ./

RUN uv sync --locked --no-cache --no-dev

COPY app ./app

RUN useradd -m appuser
USER appuser

EXPOSE 8000

CMD .venv/bin/alembic upgrade head && \
    .venv/bin/gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
