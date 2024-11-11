FROM python:3.11-slim-bookworm

# Install dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libgl1 \
    libglib2.0-0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Use uv to install python dependencies.
WORKDIR /app
COPY pyproject.toml uv.lock ./

# Mounting the uv binary like this means that it wont
# be left behind in the final version of the Image.
RUN --mount=from=ghcr.io/astral-sh/uv,source=/uv,target=/bin/uv \
    uv sync --no-dev --frozen --no-install-project --no-editable --no-cache

# Add source code
COPY . /app/

# Install the project
RUN --mount=from=ghcr.io/astral-sh/uv,source=/uv,target=/bin/uv \
    uv sync --no-dev --frozen --no-editable --no-cache

# Activate the virtual environment
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Run the application
ENTRYPOINT ["python", "-m", "stream.stream"]
