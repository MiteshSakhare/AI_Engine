# --------------------------------------------------
# BASE IMAGE
# --------------------------------------------------
FROM python:3.10-slim

# --------------------------------------------------
# ENVIRONMENT
# --------------------------------------------------
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app \
    PYTHONFAULTHANDLER=1 \
    MPLCONFIGDIR=/tmp/matplotlib

# --------------------------------------------------
# SYSTEM DEPENDENCIES
# --------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    curl \
    libgomp1 \
    ca-certificates \
    build-essential \
    tini \
    && rm -rf /var/lib/apt/lists/*

# --------------------------------------------------
# PYTHON DEPENDENCIES
# --------------------------------------------------
COPY requirements.txt requirements-dev.txt ./

RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# --------------------------------------------------
# APP SOURCE
# --------------------------------------------------
COPY . .

# Make entrypoint script executable
RUN chmod +x entrypoint.sh

# --------------------------------------------------
# ✅ ML ARTIFACT DIRECTORIES (CRITICAL)
# --------------------------------------------------
# Explicit creation avoids permission issues when the
# non-root user writes logs / models / datasets.
RUN mkdir -p \
    logs \
    ml_artifacts/data \
    ml_artifacts/discovery/models \
    ml_artifacts/discovery/preprocessors \
    ml_artifacts/benchmark/models \
    ml_artifacts/benchmark/preprocessors \
    ml_artifacts/strategy/models \
    ml_artifacts/strategy/preprocessors \
    ml_artifacts/feedback \
    ml_artifacts/tmp \
    ml_artifacts/cache

# --------------------------------------------------
# 🔒 SECURITY (Non-Root User)
# --------------------------------------------------
RUN useradd -m bravola && \
    chown -R bravola:bravola /app

USER bravola

# --------------------------------------------------
# RUNTIME
# --------------------------------------------------
EXPOSE 8000

# --------------------------------------------------
# ENTRYPOINT & START SERVER
# --------------------------------------------------
ENTRYPOINT ["tini", "--", "./entrypoint.sh"]
