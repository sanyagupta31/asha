FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download spacy model at build time
RUN python -m spacy download en_core_web_sm

COPY src ./src
COPY data /app/data

CMD ["uvicorn", "src.ragi:app", "--host", "0.0.0.0", "--port", "8000"]
