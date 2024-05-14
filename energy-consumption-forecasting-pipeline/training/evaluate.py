import argparse
import logging
from pathlib import Path
from typing import Optional
import mlflow
import mlflow.exceptions
from mlflow.tracking import MlflowClient
from neuralprophet import utils as np_utils
from shared import config
from training.train import (
    evaluate_forecast,
    load_data,
    forecast
)
from neuralprophet import NeuralProphet
import pandas as pd
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def evaluate(
    train_data_dir: Path,
    run_json: Path,
    prev_run_id: Optional[str],
    output_file: Path
):
    df_valid = load_data(train_data_dir / 'valid.csv')
    df_test = load_data(train_data_dir / 'test.csv')
    df_test_lags = pd.concat([df_valid.tail(config.N_LAGS), df_test])
    run = get_run(run_json)
    model_version = run['model_version']
    new_model_metrics = run['metrics']

    mlflow.set_tracking_uri(config.MLFLOW_TRACKING_URI)
    mlflow_client = MlflowClient()

    model = load_model(mlflow_client, prev_run_id)
    if model is None:
        update_model_stage(mlflow_client, model_version)
        set_evaluation_result(True, output_file)
        logger.info('Skipping evaluation and updating model stage')
        return

    forecasts = forecast(df_test=df_test_lags, model=model)
    prev_model_metrics = evaluate_forecast(
        actual=df_test.y.values,
        preds=forecasts.yhat.values
    )

    evaluation_passed = False
    new_mae = new_model_metrics['MAE']
    prev_mae = prev_model_metrics['MAE']

    logger.info(f'New model MAE: {new_mae}')
    logger.info(f'Prev model MAE: {prev_mae}')

    if new_mae < prev_mae or abs(prev_mae - new_mae) < 0.01:
        evaluation_passed = True
        update_model_stage(mlflow_client, model_version)

    set_evaluation_result(evaluation_passed, output_file)


def load_model(
    mlflow_client: MlflowClient,
    run_id: Optional[str]
) -> Optional[NeuralProphet]:
    if run_id and len(run_id) > 0:
        model_path = mlflow_client.download_artifacts(run_id, 'model/model.np')
        return np_utils.load(model_path)
    return None


def set_evaluation_result(passed: bool, output_file: Path):
    output_file.write_text(json.dumps({'evaluation_passed': passed}))


def update_model_stage(mlflow_client: MlflowClient, model_version: str):
    mlflow_client.transition_model_version_stage(
        config.MODEL_NAME,
        model_version,
        config.MLFLOW_PROD_STAGE,
        archive_existing_versions=True
    )


def get_run(run_path: Path):
    with run_path.open('r') as f:
        return json.load(f)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--train_data_dir', type=Path)
    parser.add_argument('--run_json', type=Path)
    parser.add_argument('--prev_run_id', type=str, default=None)
    parser.add_argument('--output_file', type=Path)
    args = parser.parse_args()

    evaluate(args.train_data_dir, args.run_json, args.prev_run_id, args.output_file)
