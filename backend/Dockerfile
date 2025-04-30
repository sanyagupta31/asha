FROM python:3.11-slim@sha256:82c07f2f6e35255b92eb16f38dbd22679d5e8fb523064138d7c6468e7bf0c15b

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download spacy model at build time
RUN python -m spacy download en_core_web_sm

COPY src ./src
COPY data /app/data

CMD ["uvicorn", "src.appp:app", "--host", "0.0.0.0", "--port", "8000"]
