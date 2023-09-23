FROM python:3.10-slim

# Install git for MLFlow client
RUN apt-get update && apt-get install git -y && \
    pip install -U --no-cache-dir pip

WORKDIR /app

COPY requirements.txt .

RUN --mount=type=cache,target=/root/.cache \
    pip install -r requirements.txt

COPY training training
COPY inference inference
COPY pipeline pipeline
COPY shared shared
