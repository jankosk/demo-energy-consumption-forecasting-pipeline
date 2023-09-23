from kfp import Client as KfpClient
from .config import EXPERIMENT_NAME


def get_experient_id(kfp_client: KfpClient) -> str:
    experiment = kfp_client.get_experiment(experiment_name=EXPERIMENT_NAME)
    experiment_id = experiment.experiment_id
    if experiment_id is None:
        raise Exception(f'Kubeflow experiment {EXPERIMENT_NAME} not found')
    return experiment_id
