# Lightweight Python image
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Install basic OS deps (certs, locales, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates build-essential git \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first (leverages Docker layer cache)
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy source
COPY src ./src

# Make src importable
ENV PYTHONPATH=/app

# Expose FastAPI port
EXPOSE 8000

# Start the API
CMD ["uvicorn", "src.agent_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
