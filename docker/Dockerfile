# Multi-stage build: compile stage + runtime stage
FROM --platform=linux/amd64 python:3.12-slim as builder

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
COPY src/requirements.txt .

# Build wheels for faster installation
RUN pip install --user --no-cache-dir --upgrade pip wheel \
    && pip wheel --no-cache-dir --no-deps --wheel-dir /build/wheels -r requirements.txt

# Runtime stage
FROM --platform=linux/amd64 python:3.12-slim

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

WORKDIR /src

# Copy wheels from builder
COPY --from=builder /build/wheels /tmp/wheels
COPY src/requirements.txt .

# Copy and install rl_thor for GraphTask support
COPY third_party/rl_thor /src/third_party/rl_thor

# Install wheels (no index, pre-built) and rl_thor
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-index --find-links=/tmp/wheels -r requirements.txt \
    && pip install --no-cache-dir -e /src/third_party/rl_thor \
    && rm -rf /tmp/wheels

# Copy application code
COPY src/ /src/

# Set PYTHONPATH so both top-level modules and src.* imports resolve
ENV PYTHONPATH=/src:/

# Expose FastAPI port (default 8000)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Run FastAPI server
CMD ["uvicorn", "backend.api.app:app", "--host", "0.0.0.0", "--port", "8000"]