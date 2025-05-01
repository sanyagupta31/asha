FROM python:3.11-slim

WORKDIR /app
COPY . .

# Install a simple web server
RUN pip install --no-cache-dir httpserver

# Serve frontend on port 5000
CMD ["python", "-m", "http.server", "5000"]
