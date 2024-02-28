import logging
import argparse
import pandas as pd
import time
from minio import Minio, error
from kfp import Client as KfpClient
from training.preprocess import process_df
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


def retrainer(pipeline_version: str):
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

    if should_retrain(actual, preds, len(prod_df)):
        run_pipeline(pipeline_version)
        next_date = until_date
        update_timestamp(next_date)


def should_retrain(actual, preds, all_data_len):
    data_len = min(len(actual), len(preds))
    min_len = all_data_len * 0.01
    if data_len < config.N_FORECASTS:
        return False
    forecast_actual = actual[-config.N_FORECASTS:]
    forecast = preds[-config.N_FORECASTS:]
    abs_error_exceeded = check_absolute_error(forecast_actual, forecast)
    relative_error_exceeded = check_relative_error(forecast_actual, forecast)
    if data_len < min_len:
        logger.info('Not enough data for retraining')
        return False
    return abs_error_exceeded and relative_error_exceeded


def check_absolute_error(actual, preds) -> bool:
    MAE = float(metrics.mean_absolute_error(actual, preds))
    MAX_MAE = 0.05
    logger.info(f'MAE: {MAE} / {MAX_MAE}')
    return MAE > MAX_MAE


def check_relative_error(actual, preds) -> bool:
    MAPE = float(metrics.mean_absolute_percentage_error(actual, preds)) * 100
    MAX_MAPE = 20
    logger.info(f'MAPE: {MAPE} / {MAX_MAPE}')
    return MAPE > MAX_MAPE


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
        job_name=f'Retrain {datetime.now()}',
        pipeline_id=pipeline_id,
        version_id=version.pipeline_version_id,
        pipeline_root=config.PIPELINE_ROOT,
        params=params,
        enable_caching=False,
    )


def update_timestamp(timestamp: datetime):
    with open(LAST_RUN_FILE_PATH, 'a') as f:
        ts = timestamp.isoformat()
        logger.info(f'Updating timestamp with {ts}')
        f.write(ts + '\n')


def get_timestamp() -> datetime:
    with open(LAST_RUN_FILE_PATH, 'r') as f:
        lines = f.readlines()
        ts = lines[-1].strip()
        return datetime.fromisoformat(ts)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--pipeline_version', type=str)
    args = parser.parse_args()

    while True:
        retrainer(args.pipeline_version)
        time.sleep(5)
