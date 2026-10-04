FROM python:3.14-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY requirements.lock ./
RUN pip install -r requirements.lock
COPY pyproject.toml alembic.ini README.md ./
COPY app ./app
RUN pip install --no-deps --no-build-isolation . \
    && useradd --create-home --uid 10001 app \
    && mkdir -p /data/storage && chown -R app:app /data/storage
USER app
EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:create_app --factory --host 0.0.0.0 --port 8000"]
