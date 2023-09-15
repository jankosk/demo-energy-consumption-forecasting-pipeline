import argparse
import uuid
from pathlib import Path
from kfp import Client, compiler, dsl, kubernetes
from kfp.components import YamlComponent, load_component_from_file
from shared import config
from typing import Any

COMPONENTS_PATH = Path(__file__).parent / 'components'
PIPELINE_PATH = Path('/tmp') / 'pipeline.yaml'
IMAGE_URL = '127.0.0.1:5001/training'
MLFLOW_S3_ENDPOINT_URL = 'http://mlflow-minio-service.mlflow.svc.cluster.local:9000'  # noqa: E501


def load_component(
    filename: str,
    image_digest: str
) -> YamlComponent:
    filepath = COMPONENTS_PATH / filename
    component = load_component_from_file(str(filepath))
    image = f'{IMAGE_URL}@{image_digest}'
    container = component.component_spec.implementation.container
    if container:
        container.image = image
    return component


def create_pipeline_func(image_digest: str, pipeline_version: str):
    @dsl.pipeline(name='Training')
    def pipeline(
        bucket_name: str,
        file_name: str,
        experiment_name: str
    ):
        pull_data = load_component('pull_data_component.yaml', image_digest)
        pull_data_step = pull_data(
            bucket_name=bucket_name,
            file_name=file_name
        )

        preprocess = load_component('preprocess_component.yaml', image_digest)
        preprocess_step = preprocess(
            input_path=pull_data_step.output
        )

        train = load_component('train_component.yaml', image_digest)
        train_step = train(
            train_data_dir=preprocess_step.output,
            experiment_name=experiment_name
        )
        kubernetes.use_secret_as_env(
            train_step,
            secret_name='aws-secret',
            secret_key_to_env={
                'AWS_ACCESS_KEY_ID': 'AWS_ACCESS_KEY_ID',
                'AWS_SECRET_ACCESS_KEY': 'AWS_SECRET_ACCESS_KEY'
            }
        )

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
        deploy_task = deploy_trigger(
            image=image,
            pipeline_version=pipeline_version
        )
        deploy_task.after(deploy_isvc_step)

    return pipeline


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--image_digest', type=str)
    args = parser.parse_args()
    image_digest = args.image_digest
    pipeline_version = str(uuid.uuid4())

    client = Client()
    pipeline_compiler = compiler.Compiler()

    pipeline: Any = create_pipeline_func(
        image_digest=image_digest,
        pipeline_version=pipeline_version
    )
    pipeline_compiler.compile(
        pipeline_func=pipeline,
        package_path=str(PIPELINE_PATH)
    )

    arguments = {
        "bucket_name": config.BUCKET_NAME,
        "file_name": config.PROD_DATA,
        "experiment_name": config.EXPERIMENT_NAME,
    }
    client.create_run_from_pipeline_package(
        str(PIPELINE_PATH),
        arguments=arguments,
        experiment_name=config.EXPERIMENT_NAME,
        pipeline_root=config.PIPELINE_ROOT,
        enable_caching=True
    )
    client.upload_pipeline_version(
        pipeline_package_path=str(PIPELINE_PATH),
        pipeline_version_name=pipeline_version,
        pipeline_name=config.PIPELINE_NAME
    )
