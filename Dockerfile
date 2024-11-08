FROM python:3.11-slim-bookworm

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    git \
    libpq-dev \
    make \
    pkg-config \
    libgl1 \
    libglib2.0-0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Install dependencies
WORKDIR /app
COPY pyproject.toml uv.lock README.md* ./
RUN uv sync --no-dev --frozen

# Add source code
COPY ./src/ /app/src/

# Run the application
ENTRYPOINT ["uv", "run", "python", "/app/src/stream/stream.py"]
