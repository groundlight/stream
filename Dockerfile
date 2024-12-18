# Stage 1: Build environment
FROM python:3.11-slim-bookworm AS builder

# Install dependencies and clean up
RUN apt-get update && \
    apt-get install -y gcc && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Use uv to install python dependencies.
WORKDIR /app
COPY pyproject.toml uv.lock ./

# Mounting the uv binary like this means that it wont
# be left behind in the final version of the Image.
RUN --mount=from=ghcr.io/astral-sh/uv,source=/uv,target=/bin/uv \
    uv sync --no-dev --frozen --no-install-project --no-editable --no-cache

# Add source code
COPY . /app/

# Stage 2: Final image
FROM python:3.11-slim-bookworm

# Install OpenGL and GLib libraries
RUN apt-get update && \
    apt-get install -y libgl1 libglib2.0-0 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy only the necessary files from the builder stage
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src /app/src
COPY --from=builder /app/pyproject.toml /app/pyproject.toml
COPY --from=builder /app/uv.lock /app/uv.lock

# Install the project in the final stage
RUN --mount=from=ghcr.io/astral-sh/uv,source=/uv,target=/bin/uv \
    uv sync --no-dev --frozen --no-editable --no-cache

# Activate the virtual environment
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Run the application
ENTRYPOINT ["python", "-m", "stream"]