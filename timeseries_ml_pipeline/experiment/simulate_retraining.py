from minio import Minio
from kfp import Client
from kfp_server_api import V2beta1Run, V2beta1RuntimeState
from datetime import datetime, timedelta
from pathlib import Path
from shared.config import BUCKET_NAME, PROD_DATA, MODEL_NAME
from shared.utils import get_experient_id
from typing import List
import pandas as pd
import json
import requests
import logging
import time

SERVICE_NAME = 'test-isvc.kserve-inference.example.com'
ALL_DATA_SET = 'data.csv'
FIRST_DATE = datetime.fromisoformat('2019-04-29T15:00:00')
LAST_DATE = datetime.fromisoformat('2022-04-01T00:00:00')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

all_df = pd.read_csv(
    Path(__file__).parent / ALL_DATA_SET,
    parse_dates=['Time']
)

kfp_client = Client()

minio_client = Minio(
    endpoint='localhost:9000',
    access_key='minioadmin',
    secret_key='minioadmin',
    secure=False
)


def update_ground_truth(curr_date: datetime):
    data_path = '/tmp/prod_data.csv'
    minio_client.fget_object(BUCKET_NAME, PROD_DATA, data_path)
    prod_df = pd.read_csv(data_path, parse_dates=['Time'])

    next_date = curr_date + timedelta(days=1)
    update_df = all_df[(all_df['Time'] >= curr_date) &
                       (all_df['Time'] <= next_date)]
    updated_data = pd.concat([prod_df, update_df])
    logger.info(f'UPDATE GROUND TRUTH\n{updated_data.tail().to_string()}')

    updated_data.to_csv(data_path, index=False)
    minio_client.fput_object(
        BUCKET_NAME,
        PROD_DATA,
        data_path
    )


def get_forecast(from_date: datetime) -> pd.DataFrame:
    headers = {'Host': SERVICE_NAME, 'Content-type': 'application/json'}
    data = json.dumps(f'{{"from_date": "{from_date}"}}')
    res = requests.post(
        url=f'http://localhost:8080/v1/models/{MODEL_NAME}:predict',
        data=data,
        headers=headers
    )
    forecast = res.json()
    forecast_df = pd.DataFrame.from_dict(forecast)
    logger.info(f'FORECAST\n{forecast_df.tail().to_string()}')
    return forecast_df


def is_active_run(run: V2beta1Run):
    return (run.state == V2beta1RuntimeState.RUNNING or
            run.state == V2beta1RuntimeState.PENDING)


def get_active_run(experiment_id: str) -> V2beta1Run | None:
    res = kfp_client.list_runs(experiment_id=experiment_id)
    runs: List[V2beta1Run] = res.runs if res.runs else []
    return next(
        (run for run in runs if is_active_run(run)),
        None
    )


def run_experiment():
    experiment_str = get_experient_id(kfp_client)
    curr_date = FIRST_DATE
    while curr_date < LAST_DATE:
        logger.info(f'DAY {curr_date.isoformat()}')
        active_run = get_active_run(experiment_str)
        if active_run is not None:
            logger.info('Waiting for retraining to complete...')
            kfp_client.wait_for_run_completion(
                run_id=str(active_run.run_id),
                timeout=60 * 5
            )
        get_forecast(curr_date)
        update_ground_truth(curr_date)
        curr_date = curr_date + timedelta(days=1)
        time.sleep(60)


if __name__ == '__main__':
    run_experiment()
