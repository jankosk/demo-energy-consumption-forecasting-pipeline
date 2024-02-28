from kfp import Client as KfpClient
from .config import EXPERIMENT_NAME
import pandas as pd


def get_experient_id(kfp_client: KfpClient) -> str:
    experiment = kfp_client.get_experiment(experiment_name=EXPERIMENT_NAME)
    experiment_id = experiment.experiment_id
    if experiment_id is None:
        raise Exception(f'Kubeflow experiment {EXPERIMENT_NAME} not found')
    return experiment_id


def handle_zeros_and_negatives(df: pd.DataFrame, col: str, min: float = 1e-5):
    df.loc[df[col] <= 0.0, col] = min
    return df
