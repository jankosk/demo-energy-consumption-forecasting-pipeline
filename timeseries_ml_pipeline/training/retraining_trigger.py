import os
import logging
import pandas as pd
from minio import Minio
from .preprocess import process_df
from pathlib import Path
from datetime import datetime

VOLUME_MOUNT_PATH = Path('/data')
LAST_RUN_FILE_PATH = VOLUME_MOUNT_PATH / 'last_run.timestamp'
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


def retraining_trigger():
    data_predictions = 'predictions.csv'
    data_prod = 'data.csv'
    minio_client = Minio(
        endpoint=S3_MINIO_ENDPOINT,
        access_key=ACCESS_KEY,
        secret_key=SECRET_KEY,
        secure=False
    )
    minio_client.fget_object(BUCKET_NAME, PROD_PREDICTIONS, data_predictions)
    predictions_df = pd.read_csv(data_predictions, parse_dates=['ds'])

    minio_client.fget_object(BUCKET_NAME, PROD_DATA_SET, data_prod)
    prod_df = pd.read_csv(data_prod)
    prod_df = process_df(prod_df)

    logger.info(f'PROD_DF:\n{prod_df.head().to_string()}')
    logger.info(f'PREDICTIONS_DF:\n{predictions_df.head().to_string()}')

    if not LAST_RUN_FILE_PATH.exists():
        first_entry = prod_df.iloc[0].ds
        update_timestamp(first_entry)

    timestamp = get_timestamp()
    logger.info(f'TIMESTAMP {timestamp.isoformat()}')


def update_timestamp(timestamp: datetime):
    with open(LAST_RUN_FILE_PATH, 'w') as f:
        ts = timestamp.isoformat()
        logger.info(f'Updating timestamp with {ts}')
        f.write(ts)


def get_timestamp() -> datetime:
    with open(LAST_RUN_FILE_PATH, 'r') as f:
        data = f.read()
        return datetime.fromisoformat(data)


if __name__ == '__main__':
    logger.info('Running retraining trigger...')
    retraining_trigger()
