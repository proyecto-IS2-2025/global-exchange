# syntax=docker/dockerfile:1.7

# Base image
ARG PYTHON_VERSION=3.13
FROM python:3.13-slim AS app

# Environment settings
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VERSION=2.0.1 \
    PATH="/home/appuser/.local/bin:${PATH}"

WORKDIR /app

# System deps (kept minimal because psycopg[binary] is used)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir "poetry==${POETRY_VERSION}"

# Only copy dependency files first to leverage Docker layer caching
COPY pyproject.toml poetry.lock* ./

# Configure Poetry to install into the system environment (no venvs)
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

# Copy application source
COPY . .

# Build documentation and set up user permissions
# Si no usas Sphinx, puedes eliminar esta línea
RUN poetry run sphinx-build -M html "$(pwd)/docs/source" "$(pwd)/docs/_build" \
    && chmod +x scripts/entrypoint.sh \
    && useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app

USER appuser

# Default port (can be overridden with PORT env var)
EXPOSE 8000

# Entrypoint runs migrations and starts Django dev server (per README)
ENTRYPOINT ["/app/scripts/entrypoint.sh"]