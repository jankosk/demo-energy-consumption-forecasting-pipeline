import logging
import argparse
import pandas as pd
import numpy as np
import time
from minio import Minio, error
from kfp import Client as KfpClient
from .preprocess import process_df
from shared import config
from shared.utils import get_experient_id
from pathlib import Path
from datetime import datetime
from sklearn import metrics

VOLUME_MOUNT_PATH = Path('/data')
LAST_RUN_FILE_PATH = VOLUME_MOUNT_PATH / 'last_run.timestamp'
KFP_URL = 'http://ml-pipeline-ui.kubeflow'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def retraining_trigger(pipeline_version: str):
    data_predictions = 'predictions.csv'
    data_prod = 'data.csv'
    minio_client = Minio(
        endpoint=config.S3_MINIO_ENDPOINT,
        access_key=config.MINIO_ACCESS_KEY,
        secret_key=config.MINIO_SECRET_KEY,
        secure=False
    )

    minio_client.fget_object(config.BUCKET_NAME, config.PROD_DATA, data_prod)
    try:
        minio_client.fget_object(
            config.BUCKET_NAME,
            config.PREDICTIONS_DATA,
            data_predictions
        )
    except error.S3Error:
        logger.error(f'File {config.PREDICTIONS_DATA} does not exist')
        return

    predictions_df = pd.read_csv(data_predictions, parse_dates=['ds'])
    prod_df = pd.read_csv(data_prod)
    prod_df = process_df(prod_df)

    if not LAST_RUN_FILE_PATH.exists():
        first_entry = predictions_df.iloc[0].ds
        update_timestamp(first_entry)

    from_date = get_timestamp()
    until_date = predictions_df.iloc[-1].ds
    logger.info(f'{from_date.isoformat()} - {until_date.isoformat()}')
    last_prod_entry_date = prod_df.iloc[-1].ds
    if last_prod_entry_date < until_date:
        logger.info('Skipping... Waiting for more ground truth data.')
        return False

    predictions_df = predictions_df[predictions_df.ds > from_date]
    prod_df = prod_df[(prod_df.ds > from_date) &
                      (prod_df.ds <= until_date)]
    actual = prod_df.y.values
    preds = predictions_df.yhat.values

    if should_retrain(actual, preds):
        run_pipeline(pipeline_version)
        next_date = until_date
        update_timestamp(next_date)


def should_retrain(actual, predictions):
    diff = np.sort(np.abs(actual - predictions))
    if len(diff) <= 24:
        return False
    MAE = metrics.mean_absolute_error(actual, predictions)
    MAE_THRESHOLD = 0.05
    MAX_N_ERROR = diff[-24:].mean()
    MAX_N_ERROR_THRESHOLD = 0.1
    logger.info(f'MAE: {MAE}')
    logger.info(f'MAX AVG ERROR: {MAX_N_ERROR}')
    return MAE > MAE_THRESHOLD or MAX_N_ERROR > MAX_N_ERROR_THRESHOLD


def run_pipeline(version_name: str):
    client = KfpClient(host=KFP_URL)
    pipeline_id = client.get_pipeline_id(config.PIPELINE_NAME)
    experiment_id = get_experient_id(client)
    if pipeline_id is None:
        raise Exception(f'Pipeline {config.PIPELINE_NAME} not found')

    res = client.list_pipeline_versions(pipeline_id, sort_by='created_at desc')
    versions = res.pipeline_versions if res.pipeline_versions else []
    version = next(
        (ver for ver in versions if ver.display_name == version_name),
        None
    )
    if version is None:
        raise Exception(f'Pipeline version {version_name} not found')

    logger.info(f'Running {config.PIPELINE_NAME}...')
    params = {
        'bucket_name': config.BUCKET_NAME,
        'file_name': config.PROD_DATA,
        'experiment_name': config.EXPERIMENT_NAME,
    }
    client.run_pipeline(
        experiment_id=experiment_id,
        job_name='Retrain',
        pipeline_id=pipeline_id,
        version_id=version.pipeline_version_id,
        pipeline_root=config.PIPELINE_ROOT,
        params=params,
        enable_caching=False,
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

    while True:
        retraining_trigger(args.pipeline_version)
        time.sleep(7)
