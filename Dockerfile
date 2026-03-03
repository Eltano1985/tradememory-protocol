FROM python:3.11-slim

LABEL maintainer="Mnemox <contact@mnemox.ai>"
LABEL description="TradeMemory Hosted API — Multi-tenant AI Trading Memory API"

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ src/
COPY hosted/ hosted/

# Create data directory for SQLite
RUN mkdir -p data

# Expose hosted API port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/api/v1/health')" || exit 1

# Run hosted API server
CMD ["uvicorn", "hosted.server:app", "--host", "0.0.0.0", "--port", "8080"]
