import os
import logging
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
from pathlib import Path
from neuralprophet import NeuralProphet, utils as np_utils
from typing import Dict
from kserve import Model, ModelServer
from shared.utils import handle_zeros_and_negatives
from training.preprocess import process_df
from shared import config
from minio import Minio, error

MODEL_URI = os.environ.get('MODEL_URI', '/mnt/models/model.np')
MODEL_VERSION = os.environ.get('MODEL_VERSION')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NeuralProphetModel(Model):
    model: NeuralProphet
    ready: bool

    def __init__(self, name: str):
        super().__init__(name)
        self.name = name
        self.minio_client = Minio(
            endpoint=config.S3_MINIO_ENDPOINT,
            access_key=config.MINIO_ACCESS_KEY,
            secret_key=config.MINIO_SECRET_KEY,
            secure=False
        )
        self.load()

    def load(self):
        logger.info(f'Loading {config.MODEL_NAME} version {MODEL_VERSION}...')
        self.model = np_utils.load(MODEL_URI)
        self.ready = True

    def predict(self, payload: bytes, _header: Dict[str, str]) -> Dict:
        data = json.loads(payload)
        from_date_param = data.get('from_date')
        from_date = datetime.fromisoformat(from_date_param)

        gt_df = self.get_ground_truth_data()

        prev_n_steps_df = self.fetch_previous_n_steps(gt_df, from_date)
        if len(prev_n_steps_df) < config.N_LAGS:
            empty_df = pd.DataFrame()
            logger.error(f'Forecast for {from_date.isoformat()} ({len(prev_n_steps_df)}) not available')  # noqa E501
            return empty_df.to_dict()

        forecast_df = self.model.make_future_dataframe(prev_n_steps_df)

        forecast = self.model.predict(forecast_df)
        min = get_lowest_non_zero_val(gt_df)
        forecast = process_forecast(forecast, min)
        self.save_forecast(forecast)

        return forecast.to_dict()

    def fetch_previous_n_steps(
        self,
        gt_df: pd.DataFrame,
        from_date: datetime
    ) -> pd.DataFrame:
        df = gt_df[['ds', 'y', 'Temp_outside']]
        prev_n_date = from_date - timedelta(hours=config.N_LAGS)
        return df[(df.ds <= from_date) & (df.ds >= prev_n_date)]

    def save_forecast(self, forecast: pd.DataFrame):
        data_path = Path('updated_predictions.csv')
        prev_prediction = self.get_previous_predictions()
        predictions = pd.concat([prev_prediction, forecast])
        predictions.to_csv(data_path, index=False)
        self.minio_client.fput_object(
            config.BUCKET_NAME,
            config.PREDICTIONS_DATA,
            data_path
        )

    def get_previous_predictions(self) -> pd.DataFrame:
        try:
            data_path = 'prev_predictions.csv'
            self.minio_client.fget_object(
                config.BUCKET_NAME,
                config.PREDICTIONS_DATA,
                data_path
            )
            return pd.read_csv(data_path, parse_dates=['ds'])
        except error.S3Error:
            return pd.DataFrame({'ds': [], 'yhat': []})

    def get_ground_truth_data(self) -> pd.DataFrame:
        data_path = 'ground_truth.csv'
        self.minio_client.fget_object(
            config.BUCKET_NAME,
            config.PROD_DATA,
            data_path
        )
        df = pd.read_csv(data_path)
        return process_df(df)


def process_forecast(df: pd.DataFrame, min: float = 1e-2) -> pd.DataFrame:
    forecast = df.tail(config.N_FORECASTS)
    n, m = forecast.shape
    identity_matrix = np.eye(N=n, M=m, k=2, dtype=bool)
    yhat = forecast.values[identity_matrix]
    forecast = pd.DataFrame({'ds': forecast['ds'], 'yhat': yhat})
    return handle_zeros_and_negatives(forecast, 'yhat', min)


def get_lowest_non_zero_val(df: pd.DataFrame) -> float:
    non_zero_vals = df[df['y'] > 0]
    return non_zero_vals['y'].min()


if __name__ == "__main__":
    model = NeuralProphetModel(config.MODEL_NAME)
    ModelServer().start([model])
