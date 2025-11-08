FROM python:3.13-slim

WORKDIR /app

COPY ./app /app/app
COPY ./pyproject.toml /app/pyproject.toml

RUN pip install --no-cache-dir fastapi uvicorn sqlalchemy aiosqlite httpx python-multipart

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
