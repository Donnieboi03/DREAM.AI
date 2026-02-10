# Multi-stage build: compile stage + runtime stage
FROM python:3.10-slim as builder

# Build dependencies for ProcTHOR (python-fcl, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    libeigen3-dev \
    libccd-dev \
    libfcl-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY ../dreamai/requirements.txt .

# Build wheels for faster installation
RUN pip install --user --no-cache-dir --upgrade pip wheel \
    && pip wheel --no-cache-dir --no-deps --wheel-dir /build/wheels -r requirements.txt

# Runtime stage
FROM python:3.10-slim

# Runtime dependencies for AI2-THOR (headless rendering + web)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libxi6 \
    libxrandr2 \
    libxss1 \
    libxtst6 \
    libnss3 \
    libasound2 \
    ca-certificates \
    libeigen3-dev \
    libccd-dev \
    libfcl-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /dreamai

# Copy wheels from builder
COPY --from=builder /build/wheels /tmp/wheels
COPY ../dreamai/requirements.txt .

# Install wheels (no index, pre-built)
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-index --find-links=/tmp/wheels -r requirements.txt \
    && rm -rf /tmp/wheels

# Copy application code
COPY ../dreamai/ /dreamai/

# Expose FastAPI port (default 8000)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Run FastAPI server
CMD ["uvicorn", "backend.api.app:app", "--host", "0.0.0.0", "--port", "8000"]