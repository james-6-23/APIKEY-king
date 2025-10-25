# APIKEY-king Web Interface - Optimized Dockerfile
FROM python:3.11-slim

LABEL maintainer="APIKEY-king"
LABEL description="APIKEY-king - API Key Discovery Tool with Web Interface"

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    fastapi \
    uvicorn[standard] \
    pyjwt \
    websockets \
    google-generativeai>=0.8.5 \
    python-dotenv>=1.1.1 \
    requests>=2.32.4 \
    pyyaml>=6.0

# Copy project files
COPY src/ ./src/
COPY config/ ./config/
COPY web/ ./web/

# Create data directory (only need database file)
RUN mkdir -p /app/data

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Run the web server
CMD ["python", "-m", "uvicorn", "src.web.api:app", "--host", "0.0.0.0", "--port", "8000"]

