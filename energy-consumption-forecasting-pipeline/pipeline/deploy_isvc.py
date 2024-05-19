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


def deploy(run_json: Path, image: str):
    run = get_run(run_json)
    model_uri = f'{run["model_uri"]}/model.np'
    run_id = run['run_id']

    isvc_namespace = 'kserve-inference'
    isvc_name = 'energy-consumption-forecasting-isvc'

    isvc = V1beta1InferenceService(
        api_version=constants.KSERVE_V1BETA1,
        kind=constants.KSERVE_KIND,
        metadata=client.V1ObjectMeta(
            name=isvc_name,
            labels={'app': isvc_name},
            namespace=isvc_namespace,
            annotations={
                'sidecar.istio.io/inject': 'false',
                'serving.kserve.io/enable-prometheus-scraping': 'true'
            }
        ),
        spec=V1beta1InferenceServiceSpec(
            predictor=V1beta1PredictorSpec(
                service_account_name='kserve-sa',
                containers=[client.V1Container(
                    name='kserve-custom',
                    command=['python3'],
                    args=['-m', 'inference.inference_service'],
                    image=image,
                    env=[
                        client.V1EnvVar(name='STORAGE_URI', value=model_uri),
                        client.V1EnvVar(name='MODEL_VERSION', value=run_id)
                    ]
                )]
            )
        )
    )

    kserve_client = KServeClient()

    try:
        kserve_client.patch(name=isvc_name, inferenceservice=isvc)
    except RuntimeError:
        kserve_client.create(inferenceservice=isvc)


def get_run(run_path: Path):
    with run_path.open('r') as f:
        return json.load(f)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--run_json', type=Path)
    parser.add_argument('--image', type=str)
    args = parser.parse_args()

    deploy(run_json=args.run_json, image=args.image)
