import os

MODEL_NAME = 'custom-model'

BUCKET_NAME = 'mlflow'
PROD_DATA = 'data.csv'
PREDICTIONS_DATA = 'predictions.csv'

S3_MINIO_ENDPOINT = os.getenv(
    'S3_MINIO_ENDPOINT',
    'mlflow-minio-service.mlflow.svc.cluster.local:9000'
)
MINIO_ACCESS_KEY = os.getenv('ACCESS_KEY', 'minioadmin')
MINIO_SECRET_KEY = os.getenv('SECRET_KEY', 'minioadmin')
