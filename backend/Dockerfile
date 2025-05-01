FROM python:3.11-slim@sha256:82c07f2f6e35255b92eb16f38dbd22679d5e8fb523064138d7c6468e7bf0c15b

WORKDIR /app

# Copy from root context (since we’ll build from root)
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN python -m spacy download en_core_web_sm

COPY backend/src ./src
COPY data ./data

CMD ["uvicorn", "src.appp:app", "--host", "0.0.0.0", "--port", "8000"]
