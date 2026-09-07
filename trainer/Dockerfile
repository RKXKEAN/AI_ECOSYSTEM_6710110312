FROM nvidia/cuda:12.8.0-runtime-ubuntu22.04

# Avoid interactive prompts during apt install
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Install essential system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy uv from the official uv Docker image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set the working directory inside the container
WORKDIR /app

# Copy pyproject.toml first to cache package installation
COPY pyproject.toml .

# Create virtualenv with python 3.13 and install project dependencies
RUN uv venv --python 3.13 && \
    uv pip install --no-cache-dir -r pyproject.toml

# Copy the rest of the application code
COPY . .

# Set environment PATH so the virtual environment's executables are preferred
ENV PATH="/app/.venv/bin:$PATH"

# Run the arq worker
CMD ["arq", "worker.WorkerSettings"]
