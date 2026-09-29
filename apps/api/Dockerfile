FROM python:3.11-slim

WORKDIR /app

# curl is used by the container health check
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY apps/api/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY apps/__init__.py ./apps/__init__.py
COPY apps/api ./apps/api

# Run as an unprivileged user; the database, downloads, model and backups live in /app/data
# (a mounted volume: docker-compose declares it; Railway rejects VOLUME in Dockerfiles)
RUN useradd --create-home --uid 1000 app && mkdir -p /app/data && chown app:app /app/data
USER app

ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1

EXPOSE 8000

# Exactly one worker: the scheduler runs inside the API process and must not be duplicated
CMD ["uvicorn", "apps.api.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--proxy-headers"]
