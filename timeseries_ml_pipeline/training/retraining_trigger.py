import os
import logging
import pandas as pd
from minio import Minio
from training.preprocess import process_df

PROD_DATA_SET = '1_data.csv'
PROD_PREDICTIONS = 'predictions.csv'
BUCKET_NAME = 'mlflow'
S3_MINIO_ENDPOINT = os.getenv(
    'S3_MINIO_ENDPOINT',
    'mlflow-minio-service.mlflow.svc.cluster.local:9000'
)
ACCESS_KEY = os.getenv('ACCESS_KEY', 'minioadmin')
SECRET_KEY = os.getenv('SECRET_KEY', 'minioadmin')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def hello():
    logger.info('HELLO WORLD')


def retraining_trigger():
    data_predictions = 'ground_truth.csv'
    data_prod = 'data.csv'
    minio_client = Minio(
        endpoint=S3_MINIO_ENDPOINT,
        access_key=ACCESS_KEY,
        secret_key=SECRET_KEY,
        secure=False
    )
    minio_client.fget_object(BUCKET_NAME, PROD_PREDICTIONS, data_predictions)
    predictions_df = pd.read_csv(data_predictions)
    predictions_df = process_df(predictions_df)

    minio_client.fget_object(BUCKET_NAME, PROD_DATA_SET, data_prod)
    prod_df = pd.read_csv(data_prod)
    prod_df = process_df(prod_df)

    logger.info(f'PROD_DF:\n{prod_df.to_string()}')
    logger.info(f'PREDICTIONS_DF:\n{predictions_df.to_string()}')


if __name__ == 'main':
    hello()
