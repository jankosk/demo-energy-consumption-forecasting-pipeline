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
from training.preprocess import process_df
from shared import config
from minio import Minio, error

MODEL_URI = os.environ.get('MODEL_URI', '/mnt/models/model.np')
MODEL_VERSION = os.environ.get('MODEL_VERSION')
PERIODS = 24

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NeuralProphetModel(Model):
    model: NeuralProphet
    read: bool

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

        prev_n_steps_df = self.fetch_previous_n_steps(from_date)
        if len(prev_n_steps_df) < PERIODS:
            empty_df = pd.DataFrame()
            logger.error(f'Forecast for {from_date.isoformat()} ({len(prev_n_steps_df)}) not available')  # noqa E501
            return empty_df.to_dict()

        forecast_df = self.model.make_future_dataframe(prev_n_steps_df)

        forecast = self.model.predict(forecast_df)
        forecast = self.process_forecast(forecast)
        self.save_forecast(forecast)

        return forecast.to_dict()

    def fetch_previous_n_steps(self, from_date: datetime) -> pd.DataFrame:
        data_path = 'ground_truth.csv'
        self.minio_client.fget_object(
            config.BUCKET_NAME,
            config.PROD_DATA,
            data_path
        )
        df = pd.read_csv(data_path)
        df = process_df(df)
        df = df[['ds', 'y', 'Temp_outside']]
        prev_n_date = from_date - timedelta(hours=PERIODS)

        return df[(df.ds <= from_date) & (df.ds >= prev_n_date)]

    def process_forecast(self, df: pd.DataFrame) -> pd.DataFrame:
        forecast = df.tail(PERIODS)
        n, m = forecast.shape
        identity_matrix = np.eye(N=n, M=m, k=2, dtype=bool)
        yhat = forecast.values[identity_matrix]
        return pd.DataFrame({'ds': forecast['ds'], 'yhat': yhat})

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


if __name__ == "__main__":
    model = NeuralProphetModel(config.MODEL_NAME)
    ModelServer().start([model])
