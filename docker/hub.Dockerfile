FROM python:3.12-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

COPY pyproject.toml uv.lock ./
COPY hub/ hub/
RUN uv sync --no-dev --frozen

RUN useradd -m user && mkdir -p /app/data && chown -R user:user /app/data
USER user

EXPOSE 8000
CMD ["uv", "run", "uvicorn", "hub.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

