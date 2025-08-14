FROM python:3.9-slim

WORKDIR /app
COPY . .

ENV PYTHONPATH=/app

RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir fastapi sqlalchemy psycopg2-binary uvicorn

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]