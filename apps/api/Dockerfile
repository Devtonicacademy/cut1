FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (build-essential needed for some scipy/numpy builds if wheels not present)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency requirements
COPY apps/api/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY apps/api/app ./apps/api/app

# Set PYTHONPATH so absolute imports like `apps.api.app...` work smoothly
ENV PYTHONPATH=/app
ENV PORT=8000

EXPOSE 8000

CMD ["uvicorn", "apps.api.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
