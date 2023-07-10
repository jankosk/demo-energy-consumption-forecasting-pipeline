import os
import logging
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
from neuralprophet import NeuralProphet, utils as np_utils
from typing import Dict
from kserve import Model, ModelServer
from training.preprocess import process_df
from training.pull_data import pull_data

MODEL_URI = os.environ.get('MODEL_URI', '/mnt/models/model.np')
BUCKET_NAME = 'mlflow'
PROD_DATA_SET = '1_data.csv'
PERIODS = 24

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NeuralProphetModel(Model):
    model: NeuralProphet
    read: bool

    def __init__(self, name: str):
        super().__init__(name)
        self.name = name
        self.load()

    def load(self):
        self.model = np_utils.load(MODEL_URI)
        self.ready = True

    def predict(self, payload: Dict, header: Dict[str, str]) -> Dict:
        logging.info(f'PAYLOAD: {str(payload)}')
        from_date_param = payload.get('from_date')
        from_date = datetime.now()
        if from_date_param is not None:
            from_date = datetime.fromisoformat(from_date_param)
        prev_n_steps_df = self.fetch_previous_n_steps(from_date)
        forecast_df = self.model.make_future_dataframe(prev_n_steps_df)
        logging.info(f'FORECAST DF:\n{forecast_df.to_string()}')
        forecast = self.model.predict(forecast_df)
        forecast = self.process_forecast(forecast)
        logging.info(f'FORECAST:\n{forecast.to_string()}')
        result = forecast.to_dict()
        return result

    def fetch_previous_n_steps(self, from_date: datetime) -> pd.DataFrame:
        data_path = Path('ground_truth.csv')
        pull_data(BUCKET_NAME, PROD_DATA_SET, data_path)
        df = pd.read_csv(data_path)
        df = process_df(df)
        df = df[['ds', 'y', 'Temp_outside']]
        idx = df[df.ds == from_date].index[0]
        from_idx = idx - PERIODS
        df = df.iloc[from_idx:idx]
        logging.info(f'HISTORY DATA FRAME:\n{df.to_string()}')
        return df

    def process_forecast(self, df: pd.DataFrame) -> pd.DataFrame:
        forecast = df.tail(PERIODS)
        n, m = forecast.shape
        identity_matrix = np.eye(N=n, M=m, k=2, dtype=bool)
        yhat = forecast.values[identity_matrix]
        return pd.DataFrame({'ds': forecast['ds'], 'yhat': yhat})


if __name__ == "__main__":
    model = NeuralProphetModel("custom-model")
    ModelServer().start([model])
