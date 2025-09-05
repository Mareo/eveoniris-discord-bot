FROM python:3.13

ENV PATH="/app/.venv/bin:$PATH"
ENV UV_CACHE_DIR=/var/cache/uv
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_SYSTEM_PYTHON=1

WORKDIR /app

RUN --mount=from=ghcr.io/astral-sh/uv:0.8.15,source=/uv,target=/bin/uv \
    --mount=type=cache,target=/var/cache/uv \
    --mount=type=bind,source=./uv.lock,target=uv.lock \
    --mount=type=bind,source=./pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project

COPY . /app

RUN --mount=from=ghcr.io/astral-sh/uv:0.8.15,source=/uv,target=/bin/uv \
    --mount=type=cache,target=/var/cache/uv \
    uv sync --locked

ENTRYPOINT python3 -m main
