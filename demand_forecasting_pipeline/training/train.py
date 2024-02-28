import os
import logging
import argparse
import json
from typing import Dict
from pathlib import Path
from neuralprophet import NeuralProphet, utils as np_utils
import mlflow
import pandas as pd
from sklearn import metrics
import matplotlib.pyplot as plt
from inference.inference_service import process_forecast
from shared.config import N_FORECASTS, N_LAGS
from torchmetrics.regression import mae, mape

MLFLOW_TRACKING_URI = os.getenv(
    'MLFLOW_TRACKING_URI',
    'http://mlflow.mlflow.svc.cluster.local:5000'
)

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
            n_lags=N_LAGS,
            impute_missing=True,
            yearly_seasonality=True,
            weekly_seasonality=True,
            collect_metrics={
                'MAPE': mape.MeanAbsolutePercentageError(),
                'MAE': mae.MeanAbsoluteError()
            }
        )
        model.add_country_holidays(country_name='Finland')
        model.add_future_regressor('Temp_outside')

        training_metrics = model.fit(
            df=df_train,
            validation_df=df_valid,
            early_stopping=True,
            progress=None,
            freq='H'
        )
        if training_metrics is None:
            raise Exception('Failed to fit model')
        log_training_metrics(training_metrics)

        df_test_lags = pd.concat([df_valid.tail(N_LAGS), df_test])
        forecasts = forecast(df_test=df_test_lags, model=model)
        test_metrics = evaluate_forecast(
            actual=df_test.y.values,
            preds=forecasts.yhat.values)
        mlflow.log_metrics(test_metrics)

        if not output_dir.exists():
            output_dir.mkdir()

        fig, ax = plt.subplots(figsize=(15, 8))
        ax.plot(df_test.ds, df_test.y, 'r', label='Actual')
        ax.plot(forecasts.ds, forecasts.yhat, 'b', label='Forecast')
        ax.legend()

        log_model(model, output_dir)
        mlflow.log_figure(fig, 'forecast.png')

        save_run(run_id=run.info.run_id, output_dir=output_dir)


def load_data(csv_path: Path):
    df = pd.read_csv(csv_path, parse_dates=['ds'])
    df = df[['ds', 'y', 'Temp_outside']]
    return df


def forecast(df_test: pd.DataFrame, model: NeuralProphet):
    n_tests = int(N_LAGS / N_FORECASTS)
    forecasts = pd.DataFrame()
    for n in range(n_tests):
        from_idx = n * N_FORECASTS
        until_idx = from_idx + N_LAGS
        future_df = df_test.iloc[until_idx:until_idx + N_FORECASTS]
        future_temp_df = future_df[['ds', 'Temp_outside']]
        forecast_df = model.make_future_dataframe(
            df=df_test.iloc[from_idx:until_idx],
            regressors_df=future_temp_df)
        forecast = model.predict(forecast_df)
        forecast = process_forecast(forecast)
        forecasts = pd.concat([forecasts, forecast])
    return forecasts


def evaluate_forecast(preds, actual) -> Dict[str, float]:
    mae = float(metrics.mean_absolute_error(y_true=actual, y_pred=preds))
    mse = float(metrics.mean_squared_error(y_true=actual, y_pred=preds))
    mape = float(metrics.mean_absolute_percentage_error(actual, preds)) * 100
    return {'MAE': mae, 'MSE': mse, 'MAPE': mape}


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
