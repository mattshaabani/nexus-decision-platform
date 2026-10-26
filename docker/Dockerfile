# syntax=docker/dockerfile:1

# ---------- builder ----------
FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY src/ ./src/

RUN pip install --upgrade pip \
    && pip install --prefix=/install --no-cache-dir .

# ---------- runtime ----------
FROM python:3.12-slim AS runtime

WORKDIR /app

# Non-root user
RUN useradd --create-home --shell /bin/bash nexus
USER nexus

COPY --from=builder /install /usr/local
COPY --chown=nexus:nexus src/ ./src/
COPY --chown=nexus:nexus scripts/ ./scripts/

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    NEXUS_ENV=production

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')" || exit 1

CMD ["uvicorn", "nexus.entrypoints.api:app", "--host", "0.0.0.0", "--port", "8000"]