FROM python:3.11-alpine AS base
ENV PYTHONUNBUFFERED 1

FROM base AS builder
RUN apk update
ENV POETRY_VERSION=1.8.3
RUN pip install "poetry==$POETRY_VERSION"
RUN python -m venv /venv
COPY pyproject.toml poetry.lock ./
RUN poetry export -f requirements.txt | /venv/bin/pip install -r /dev/stdin --no-deps

FROM base AS app-base
RUN addgroup -S nonroot && adduser -S nonroot -G nonroot
WORKDIR /app
COPY pyproject.toml /app/
COPY src /app/src

FROM app-base AS deploy
COPY --from=builder /venv /venv
ENV PATH="/venv/bin:$PATH"
USER nonroot
CMD gunicorn src.app:create_app --bind 0.0.0.0:8080 --worker-class aiohttp.GunicornWebWorker --pythonpath src
