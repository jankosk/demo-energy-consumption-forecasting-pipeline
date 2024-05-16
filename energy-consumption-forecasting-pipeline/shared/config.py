import os

MODEL_NAME = 'energy-consumption-forecasting-model'
MLFLOW_PROD_STAGE = 'Production'
BUCKET_NAME = 'mlflow'
PROD_DATA = 'data.csv'
PREDICTIONS_DATA = 'predictions.csv'
TEMP_FORECAST_DATA = 'temp_forecast.csv'
EXPERIMENT_NAME = 'PRODUCTION'
PIPELINE_NAME = 'Energy Demand Forecasting Pipeline'
PIPELINE_ROOT = 'minio://mlpipeline/v2/artifacts'
N_FORECASTS = 24
N_LAGS = 24

S3_MINIO_ENDPOINT = os.getenv(
    'S3_MINIO_ENDPOINT',
    'mlflow-minio-service.mlflow.svc.cluster.local:9000'
)
MLFLOW_TRACKING_URI = os.getenv(
    'MLFLOW_TRACKING_URI',
    'http://mlflow.mlflow.svc.cluster.local:5000'
)
MINIO_ACCESS_KEY = os.getenv('ACCESS_KEY', 'minioadmin')
MINIO_SECRET_KEY = os.getenv('SECRET_KEY', 'minioadmin')
