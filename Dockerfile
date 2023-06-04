FROM python:3.10-slim

# Install git for MLFlow client
RUN apt-get update && apt-get install git -y && \
    pip install -U --no-cache-dir pip setuptools

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY training training
COPY pipeline pipeline
