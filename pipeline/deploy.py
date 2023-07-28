from kubernetes import client, config
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

config.load_incluster_config()


def deploy(input_dir: Path, image: str):
    run = get_run(input_dir)
    model_uri = f'{run["model_uri"]}/model.np'

    isvc_namespace = 'kserve-inference'
    isvc_name = 'test-isvc'
    job_namespace = 'retraining-job'
    job_name = 'test-job'

    batch_api = client.BatchV1Api()

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
                    command=['python'],
                    args=['-m', 'inference.np_inference_service'],
                    image=image,
                    env=[client.V1EnvVar(name='STORAGE_URI', value=model_uri)]
                )]
            )
        )
    )

    job_pod = client.V1PodSpec(
        restart_policy='Never',
        containers=([
            client.V1Container(
                name='retraining-job',
                command=['python'],
                args=['-m', 'training.retraining_trigger'],
                image=image
            )
        ])
    )

    hourly_cron = '1 * * * *'
    job = client.V1CronJob(
        metadata=client.V1ObjectMeta(
            name=job_name,
            namespace=job_namespace
        ),
        spec=client.V1CronJobSpec(
            job_template=client.V1JobTemplateSpec(
                spec=client.V1JobSpec(
                    template=client.V1PodTemplateSpec(
                        spec=job_pod
                    )
                )
            ),
            schedule=hourly_cron
        )
    )

    kserve_client = KServeClient()

    try:
        kserve_client.replace(name=isvc_name, inferenceservice=isvc)
    except RuntimeError:
        kserve_client.create(inferenceservice=isvc)

    try:
        batch_api.replace_namespaced_cron_job(
            name=job_name,
            namespace=job_namespace,
            body=job
        )
    except client.ApiException:
        batch_api.create_namespaced_cron_job(namespace=job_namespace, body=job)


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
