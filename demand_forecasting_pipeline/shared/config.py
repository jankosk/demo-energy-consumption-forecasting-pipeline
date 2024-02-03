import os

MODEL_NAME = 'demand-forecasting-model'
BUCKET_NAME = 'mlflow'
PROD_DATA = 'data.csv'
PREDICTIONS_DATA = 'predictions.csv'
EXPERIMENT_NAME = 'PRODUCTION'
PIPELINE_NAME = 'Energy Demand Forecasting Pipeline'
PIPELINE_ROOT = 'minio://mlpipeline/v2/artifacts'
N_FORECASTS = 24
N_LAGS = 24 * 7

S3_MINIO_ENDPOINT = os.getenv(
    'S3_MINIO_ENDPOINT',
    'mlflow-minio-service.mlflow.svc.cluster.local:9000'
)
MINIO_ACCESS_KEY = os.getenv('ACCESS_KEY', 'minioadmin')
MINIO_SECRET_KEY = os.getenv('SECRET_KEY', 'minioadmin')
