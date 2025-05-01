FROM python:3.11-slim@sha256:82c07f2f6e35255b92eb16f38dbd22679d5e8fb523064138d7c6468e7bf0c15b

WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY ./backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download spacy model at build time
RUN python -m spacy download en_core_web_sm

# Copy backend source code
COPY ./backend/src ./src

# Copy shared data (from the root data directory)
COPY ./data /app/data

# Note: Make sure your app filename is correct (appp.py vs app.py)
CMD ["uvicorn", "src.appp:app", "--host", "0.0.0.0", "--port", "8000"]