from kubernetes import client
from kserve import (
    constants,
    KServeClient,
    V1beta1InferenceService,
    V1beta1InferenceServiceSpec,
    V1beta1PredictorSpec
)
import json
import logging
import argparse
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def deploy(input_dir: Path, image: str):
    run = get_run(input_dir)
    model_uri = f'{run["model_uri"]}/model.np'

    isvc_namespace = 'kserve-inference'
    isvc_name = 'test-isvc'

    isvc = V1beta1InferenceService(
        api_version=constants.KSERVE_V1BETA1,
        kind=constants.KSERVE_KIND,
        metadata=client.V1ObjectMeta(
            name=isvc_name,
            namespace=isvc_namespace,
            annotations={'sidecar.istio.io/inject': 'false'}
        ),
        spec=V1beta1InferenceServiceSpec(
            predictor=V1beta1PredictorSpec(
                service_account_name='kserve-sa',
                containers=[client.V1Container(
                    name='kserve-custom',
                    command=['python3'],
                    args=['-m', 'inference.inference_service'],
                    image=image,
                    env=[client.V1EnvVar(name='STORAGE_URI', value=model_uri)]
                )]
            )
        )
    )

    kserve_client = KServeClient()

    try:
        kserve_client.patch(name=isvc_name, inferenceservice=isvc)
    except RuntimeError:
        kserve_client.create(inferenceservice=isvc)


def get_run(input_dir: Path):
    metrics_path = input_dir / 'mlflow.json'
    with metrics_path.open('r') as f:
        return json.load(f)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_dir', type=Path)
    parser.add_argument('--image', type=str)
    args = parser.parse_args()

    deploy(input_dir=args.input_dir, image=args.image)
