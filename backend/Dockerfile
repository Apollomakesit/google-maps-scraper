# ============================================================================
# LeadGen Intelligence Pipeline - Backend Dockerfile
# Runs FastAPI on Railway
# ============================================================================

# Build stage
FROM python:3.12-slim AS builder

WORKDIR /app

# Install system dependencies for building packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Build google-maps-scraper binary (rod) for API-keyless scraping
FROM golang:1.25.6-trixie AS scraper-builder

RUN go install -tags rod github.com/gosom/google-maps-scraper@latest \
    && go run github.com/go-rod/rod/lib/utils/get-browser@latest

# ============================================================================
# Production stage
# ============================================================================
FROM python:3.12-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcairo2 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libexpat1 \
    libgbm1 \
    libglib2.0-0 \
    libnspr4 \
    libnss3 \
    libpango-1.0-0 \
    libx11-6 \
    libxcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy google-maps-scraper and rod browser cache
COPY --from=scraper-builder /go/bin/google-maps-scraper /usr/bin/google-maps-scraper
COPY --from=scraper-builder /root/.cache/rod /root/.cache/rod

# Copy application code
COPY app/ ./app/

# Fixed port for predictable internal networking on Railway.
# The frontend proxy connects to this port via Railway private network.
ENV PORT=8000
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Run uvicorn on the fixed port
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--log-level", "info"]
