import os
import logging
import argparse
import json
from typing import Dict, cast
from pathlib import Path
from neuralprophet import NeuralProphet, utils as np_utils
import mlflow
import pandas as pd
from sklearn import metrics
import matplotlib.pyplot as plt

MLFLOW_TRACKING_URI = os.getenv(
    'MLFLOW_TRACKING_URI',
    'http://mlflow.mlflow.svc.cluster.local:5000'
)
N_FORECASTS = 24
N_LAGS = 24

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def train(experiment_name: str, train_data_dir: Path, output_dir: Path):
    df_train = load_data(train_data_dir / 'train.csv')
    df_valid = load_data(train_data_dir / 'valid.csv')
    df_test = load_data(train_data_dir / 'test.csv')

    os.environ['MLFLOW_S3_ENDPOINT_URL'] = 'http://mlflow-minio-service.mlflow.svc.cluster.local:9000'  # noqa: E501

    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment(experiment_name)

    with mlflow.start_run() as run:
        model = NeuralProphet(
            n_forecasts=N_FORECASTS,
            n_lags=N_LAGS
        )
        model.add_country_holidays(country_name='Finland')
        model.add_lagged_regressor('Temp_outside')

        training_metrics = model.fit(
            df=df_train,
            validation_df=df_valid,
            progress=None,
            early_stopping=False,
        )
        if training_metrics is None:
            raise Exception('Failed to fit model')
        log_training_metrics(training_metrics)

        forecast = model.predict(df_test)
        test_metrics = evaluate_forecast(
            actual=df_test.y[N_LAGS:],
            preds=forecast.yhat1[N_LAGS:]
        )
        mlflow.log_metrics(test_metrics)

        if not output_dir.exists():
            output_dir.mkdir()

        fig, ax = plt.subplots(figsize=(15, 8))
        ax.plot(df_test.ds, df_test.y, 'r', label='Actual')
        ax.plot(forecast.ds, forecast.yhat1, 'b', label='Forecast')
        ax.legend()

        log_model(model, output_dir)
        mlflow.log_figure(fig, 'forecast.png')

        save_run(run_id=run.info.run_id, output_dir=output_dir)


def load_data(csv_path: Path):
    df = pd.read_csv(csv_path)
    df = df[['ds', 'y', 'Temp_outside']]
    df['ds'] = pd.to_datetime(df['ds'])
    return df


def evaluate_forecast(preds: pd.Series, actual: pd.Series) -> Dict[str, float]:
    mae = cast(float, metrics.mean_absolute_error(y_true=actual, y_pred=preds))
    mse = cast(float, metrics.mean_squared_error(y_true=actual, y_pred=preds))
    return {'MAE': mae, 'MSE': mse}


def log_training_metrics(training_metrics: pd.DataFrame):
    *_, last_epoch_metrics = training_metrics.tail().to_dict(orient='records')
    for metric_name, val in last_epoch_metrics.items():
        mlflow.log_metric(f'TRAINING_{metric_name}', val)


def log_model(model: NeuralProphet, output_dir: Path):
    model_path = output_dir / 'model.np'
    np_utils.save(model, str(model_path))
    mlflow.log_artifact(str(model_path), artifact_path='model')


def save_run(run_id: str, output_dir: Path):
    output_file_path = output_dir / 'mlflow.json'
    model_uri = f'{mlflow.get_artifact_uri()}/model'
    contents = {
        'run_id': run_id,
        'model_uri': model_uri
    }
    output_file_path.write_text(json.dumps(contents))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--experiment_name', type=str)
    parser.add_argument('--train_data_dir', type=Path)
    parser.add_argument('--output_dir', default='./data', type=Path)
    args = parser.parse_args()

    train(
        experiment_name=args.experiment_name,
        train_data_dir=args.train_data_dir,
        output_dir=args.output_dir
    )
