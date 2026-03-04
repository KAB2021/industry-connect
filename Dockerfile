FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create entrypoint script with retry loop for alembic migrations
RUN printf '#!/bin/sh\nset -e\n\necho "Running Alembic migrations..."\nMAX_RETRIES=5\nRETRY_COUNT=0\nuntil alembic upgrade head; do\n    RETRY_COUNT=$((RETRY_COUNT + 1))\n    if [ "$RETRY_COUNT" -ge "$MAX_RETRIES" ]; then\n        echo "Alembic migration failed after $MAX_RETRIES attempts"\n        exit 1\n    fi\n    echo "Migration attempt $RETRY_COUNT failed, retrying in 2s..."\n    sleep 2\ndone\n\necho "Starting uvicorn..."\nexec uvicorn app.main:app --host 0.0.0.0 --port 8000\n' > /entrypoint.sh \
    && chmod +x /entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
