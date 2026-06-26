FROM python:3.13-slim AS builder

RUN pip install --no-cache-dir uv

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

FROM python:3.13-slim AS runtime

RUN useradd --create-home --shell /bin/bash appuser

COPY --from=builder /app/.venv /app/.venv
COPY src/ /app/src/

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/src"

WORKDIR /app
USER appuser

CMD ["python", "-m", "rag.agent.pipeline"]
