import os
import logging
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
from pathlib import Path
from neuralprophet import NeuralProphet, utils as np_utils
from typing import Dict
from kserve import Model, ModelServer, exceptions
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
        logger.info(f'Forecasting from {from_date} - {from_date + timedelta(hours=config.N_FORECASTS)}') # noqa E501

        gt_df = self.get_ground_truth_data()

        temp_forecast_df = self.get_temperature_forecast()
        prev_n_steps_df = self.fetch_previous_n_steps(gt_df, from_date)
        if len(prev_n_steps_df) < config.N_LAGS:
            logger.error(f'Previous steps unavailable\n{prev_n_steps_df.to_string()}')  # noqa E501
            raise exceptions.ApiException(
                status=400,
                reason='Previous steps unavailable'
            )
        if len(temp_forecast_df) < config.N_FORECASTS:
            logger.error(f'Temperature forecast unavailable\n{temp_forecast_df.to_string()}')  # noqa E501
            raise exceptions.ApiException(
                status=400,
                reason='Temperature forecast unavailable'
            )

        forecast_df = self.model.make_future_dataframe(
            df=prev_n_steps_df,
            regressors_df=temp_forecast_df
        )

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
        df = df[(df.ds <= from_date) & (df.ds > prev_n_date)]
        df.set_index('ds', inplace=True)
        df = df.resample('H').asfreq()
        df.reset_index(inplace=True)
        mean_temp = df['Temp_outside'].mean()
        mean_y = df['y'].mean()
        df['Temp_outside'].fillna(mean_temp)
        df['y'].fillna(mean_y)
        return df

    def get_temperature_forecast(self) -> pd.DataFrame:
        try:
            data_path = 'temp_forecast.csv'
            self.minio_client.fget_object(
                config.BUCKET_NAME,
                config.TEMP_FORECAST_DATA,
                data_path
            )
            return pd.read_csv(data_path)
        except error.S3Error:
            return pd.DataFrame({'ds': [], 'Temp_outside': []})

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
