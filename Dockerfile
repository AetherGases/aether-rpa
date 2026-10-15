FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src

# Long-running ETL worker (outbox + LISTEN/NOTIFY); it serves no port.
CMD ["python", "-m", "src.worker"]
