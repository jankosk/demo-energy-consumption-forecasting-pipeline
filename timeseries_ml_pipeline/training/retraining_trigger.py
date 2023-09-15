import logging
import argparse
import pandas as pd
import numpy as np
from minio import Minio, error
from kfp import Client as KfpClient
from .preprocess import process_df
from shared.config import (
    BUCKET_NAME,
    S3_MINIO_ENDPOINT,
    MINIO_ACCESS_KEY,
    MINIO_SECRET_KEY,
    PROD_DATA,
    PREDICTIONS_DATA,
    PIPELINE_NAME,
    EXPERIMENT_NAME,
    PIPELINE_ROOT
)
from shared.utils import get_experient_id
from pathlib import Path
from datetime import datetime

VOLUME_MOUNT_PATH = Path('/data')
LAST_RUN_FILE_PATH = VOLUME_MOUNT_PATH / 'last_run.timestamp'
KFP_URL = 'http://ml-pipeline-ui.kubeflow'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def retraining_trigger(pipeline_version: str):
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
    logger.info(f'pipeline version {pipeline_version}')
    last_prod_entry_date = prod_df.iloc[-1].ds
    if last_prod_entry_date < until_date:
        logger.info('Skipping... Waiting for more ground truth data.')
        return

    predictions_df = predictions_df[predictions_df.ds >= from_date]
    prod_df = prod_df[(prod_df.ds >= from_date) & (prod_df.ds <= until_date)]

    diff = np.abs(predictions_df.yhat.values - prod_df.y.values)
    mae = np.mean(diff)
    max_err = np.max(diff)
    logger.info(f'MAE: {mae}')
    logger.info(f'MAX ERROR: {max_err}')

    if mae > 0.04 and len(diff) > 24:
        run_pipeline(pipeline_version)
        update_timestamp(until_date)


def run_pipeline(version_name: str):
    client = KfpClient(host=KFP_URL)
    pipeline_id = client.get_pipeline_id(PIPELINE_NAME)
    experiment_id = get_experient_id(client)
    if pipeline_id is None:
        raise Exception(f'Pipeline {PIPELINE_NAME} not found')

    res = client.list_pipeline_versions(pipeline_id)
    versions = res.pipeline_versions if res.pipeline_versions else []
    version = next(
        (ver for ver in versions if ver.display_name == version_name),
        None
    )
    if version is None:
        raise Exception(f'Pipeline version {version_name} not found')

    logger.info(f'Running {PIPELINE_NAME}...')
    params = {
        "bucket_name": BUCKET_NAME,
        "file_name": PROD_DATA,
        "experiment_name": EXPERIMENT_NAME,
    }
    client.run_pipeline(
        experiment_id=experiment_id,
        job_name='Retrain',
        pipeline_id=pipeline_id,
        version_id=version.pipeline_version_id,
        pipeline_root=PIPELINE_ROOT,
        params=params,
    )


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
    parser = argparse.ArgumentParser()
    parser.add_argument('--pipeline_version', type=str)
    args = parser.parse_args()
    retraining_trigger(args.pipeline_version)
