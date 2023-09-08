import logging
import pandas as pd
import numpy as np
from minio import Minio, error
from .preprocess import process_df
from shared.config import (
    BUCKET_NAME,
    S3_MINIO_ENDPOINT,
    MINIO_ACCESS_KEY,
    MINIO_SECRET_KEY,
    PROD_DATA,
    PREDICTIONS_DATA
)
from pathlib import Path
from datetime import datetime

VOLUME_MOUNT_PATH = Path('/data')
LAST_RUN_FILE_PATH = VOLUME_MOUNT_PATH / 'last_run.timestamp'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def retraining_trigger():
    data_predictions = 'predictions.csv'
    data_prod = 'data.csv'
    minio_client = Minio(
        endpoint=S3_MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=False
    )
    try:
        minio_client.fget_object(
            BUCKET_NAME,
            PREDICTIONS_DATA,
            data_predictions
        )
    except error.S3Error:
        logger.error(f'File {PREDICTIONS_DATA} does not exist')
        return

    predictions_df = pd.read_csv(data_predictions, parse_dates=['ds'])

    minio_client.fget_object(BUCKET_NAME, PROD_DATA, data_prod)
    prod_df = pd.read_csv(data_prod)
    prod_df = process_df(prod_df)

    if not LAST_RUN_FILE_PATH.exists():
        first_entry = predictions_df.iloc[0].ds
        update_timestamp(first_entry)

    from_date = get_timestamp()
    until_date = predictions_df.iloc[-1].ds
    logger.info(f'from_date {from_date.isoformat()}')
    logger.info(f'until_date {until_date.isoformat()}')
    if prod_df.iloc[-1].ds < until_date:
        logger.info('Skipping... Waiting for more ground truth data.')
        return

    predictions_df = predictions_df[predictions_df.ds >= from_date]
    prod_df = prod_df[(prod_df.ds >= from_date) & (prod_df.ds <= until_date)]

    logger.info(f'PROD_DF \n{prod_df.head().to_string()}')
    logger.info(f'PRED_DF: \n{predictions_df.head().to_string()}')

    diff = np.abs(predictions_df.yhat.values - prod_df.y.values)

    logger.info(f'DIFF\n{diff}')


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
    retraining_trigger()
