FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc python3-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY ./backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model
RUN python -m spacy download en_core_web_sm

# Copy application code
COPY ./backend/src ./src

COPY ./data ./data

# Expose port
EXPOSE 10000

# Run FastAPI with Uvicorn
CMD ["uvicorn", "src.appp:app", "--host", "0.0.0.0", "--port", "10000"]
