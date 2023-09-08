import argparse
from collections.abc import Callable
from typing import Any
from pathlib import Path
from kfp.v2 import dsl
from kfp import Client, components, aws
from kfp.dsl import PipelineExecutionMode, ContainerOp
from shared import config

COMPONENTS_PATH = Path(__file__).parent / 'components'
IMAGE_URL = '127.0.0.1:5001/training'
EXPERIMENT_NAME = 'PRODUCTION'
MLFLOW_S3_ENDPOINT_URL = 'http://mlflow-minio-service.mlflow.svc.cluster.local:9000'  # noqa: E501


def load_component(
    filename: str,
    image_digest: str
) -> Callable[..., ContainerOp]:
    filepath = COMPONENTS_PATH / filename
    component: Any = components.load_component_from_file(str(filepath))
    image = f'{IMAGE_URL}@{image_digest}'
    component.component_spec.implementation.container.image = image
    return component


def create_pipeline_func(image_digest: str):
    @dsl.pipeline(name='Training')
    def training_pipeline(
        bucket_name: str,
        file_name: str,
        experiment_name: str
    ):
        pull_data = load_component('pull_data_component.yaml', image_digest)
        pull_data_step = pull_data(bucket_name, file_name)

        preprocess = load_component('preprocess_component.yaml', image_digest)
        preprocess_step = preprocess(
            input_path=pull_data_step.output
        )

        train = load_component('train_component.yaml', image_digest)
        train_step: ContainerOp = train(
            train_data_dir=preprocess_step.output,
            experiment_name=experiment_name
        )
        train_step.apply(aws.use_aws_secret(secret_name='aws-secret'))

        image = f'{IMAGE_URL}@{image_digest}'
        deploy_isvc = load_component(
            'deploy_isvc_component.yaml',
            image_digest
        )
        deploy_isvc_step = deploy_isvc(
            input_dir=train_step.output,
            image=image
        )

        deploy_trigger = load_component(
            'deploy_trigger_component.yaml',
            image_digest
        )
        deploy_trigger(image=image).after(deploy_isvc_step)

    return training_pipeline


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--image_digest', type=str)
    args = parser.parse_args()

    client = Client(host=None)

    arguments = {
        "bucket_name": config.BUCKET_NAME,
        "file_name": config.PROD_DATA,
        "experiment_name": EXPERIMENT_NAME,
    }

    pipeline = create_pipeline_func(image_digest=args.image_digest)

    run = client.create_run_from_pipeline_func(
        pipeline,
        arguments=arguments,
        experiment_name=EXPERIMENT_NAME,
        mode=PipelineExecutionMode.V2_COMPATIBLE,
        enable_caching=True
    )
