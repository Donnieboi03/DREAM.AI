FROM python:3.10-slim

# System deps for AI2-THOR (Unity) + headless rendering
RUN apt-get update && apt-get install -y --no-install-recommends \
    xvfb \
    xauth \
    procps \
    fluxbox \
    x11vnc \
    novnc \
    websockify \
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
    git \
  && rm -rf /var/lib/apt/lists/*
WORKDIR /dreamai

# Copy your project into the container
COPY . /dreamai

# Install python deps
# Pin ai2thor to 4.x to avoid the commit_id / build mismatch
RUN pip install --no-cache-dir --upgrade pip \
 && pip install -r dreamai/requirements.txt

COPY start_vnc.sh /dreamai/start_vnc.sh
RUN sed -i 's/\r$//' /dreamai/start_vnc.sh
RUN chmod +x /dreamai/start_vnc.sh

EXPOSE 5900 6080

CMD ["bash", "-lc", "/dreamai/start_vnc.sh"]
