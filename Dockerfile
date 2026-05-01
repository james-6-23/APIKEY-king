# APIKEY-king Web Interface - Multi-stage Dockerfile

# ---- Stage 1: Build React frontend ----
FROM node:20-alpine AS frontend
WORKDIR /fe

# Leverage layer cache: copy only manifest first
COPY frontend/package.json ./
COPY frontend/package-lock.json* ./
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

# Copy source and build
COPY frontend/ ./
RUN npm run build

# ---- Stage 2: Python runtime ----
FROM python:3.11-slim

LABEL maintainer="APIKEY-king"
LABEL description="APIKEY-king - API Key Discovery Tool with Web Interface"

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    fastapi \
    "uvicorn[standard]" \
    pyjwt \
    websockets \
    "python-dotenv>=1.1.1" \
    "requests>=2.32.4" \
    "pyyaml>=6.0"

COPY src/ ./src/
COPY config/ ./config/

# Copy built frontend from stage 1 into the directory the backend expects.
COPY --from=frontend /fe/dist ./frontend/dist

RUN mkdir -p /app/data

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

CMD ["python", "-m", "uvicorn", "src.web.api:app", "--host", "0.0.0.0", "--port", "8000"]
