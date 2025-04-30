FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/src ./src
COPY backend/data /app/data

CMD ["uvicorn", "src.ragi:app", "--host", "0.0.0.0", "--port", "8000"]
