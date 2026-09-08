FROM python:3.13-slim

WORKDIR /app

RUN pip install --no-cache-dir \
    mlflow==3.16.0 \
    psycopg2-binary \
    boto3

EXPOSE 5000

ENTRYPOINT ["mlflow", "server", "--backend-store-uri", "postgresql+psycopg2://admin:password123@postgres:5432/mlflow_db", "--default-artifact-root", "s3://mlflow-artifacts/", "--host", "0.0.0.0", "--port", "5000", "--allowed-hosts", "*"]
