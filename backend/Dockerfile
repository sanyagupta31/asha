# Use Python 3.11 slim as the base image
FROM python:3.11-slim@sha256:82c07f2f6e35255b92eb16f38dbd22679d5e8fb523064138d7c6468e7bf0c15b

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and data
COPY ./backend ./src  # Map 'backend' to '/app/src'
COPY ./data /app/data

# Command to run the application
CMD ["uvicorn", "src.ragi:app", "--host", "0.0.0.0", "--port", "8000"]
