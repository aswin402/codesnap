FROM python:3.12-slim

# Install system dependencies (Tesseract OCR)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy uv binary for fast, reliable system package installation
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Install codesnap and runtime dependencies
RUN uv pip install --system --no-cache .

ENTRYPOINT ["codesnap"]
CMD ["--help"]
