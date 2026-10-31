FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src

# Conexão PostgreSQL (mesmo cluster, dois databases). Credenciais vêm do
# ambiente em runtime (GitHub Environments / Secrets no EKS), não da imagem:
#   POSTGRES_USER, POSTGRES_PASSWORD (banco B), POSTGRES_HOST,
#   RPA_POSTGRES_USER, RPA_POSTGRES_PASSWORD (banco A),
#   POSTGRES_DB_FIRST_YEAR (banco A), POSTGRES_DB (banco B)
# Opcionais com default na imagem:
ENV POSTGRES_PORT=5432
ENV POSTGRES_SSLMODE=require

# Long-running ETL worker (outbox + LISTEN/NOTIFY); it serves no port.
CMD ["python", "-m", "src.worker"]
