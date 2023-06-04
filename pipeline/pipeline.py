import argparse
from pathlib import Path
from kfp.v2 import dsl
from kfp import Client, components, aws
from kfp.dsl import PipelineExecutionMode, ContainerOp

BUCKET_NAME = 'mlflow'
PROD_DATA_SET = '1_data.csv'
COMPONENTS_PATH = Path(__file__).parent / 'components'
IMAGE_URL = '127.0.0.1:5001/training'
EXPERIMENT_NAME = 'default'
MLFLOW_S3_ENDPOINT_URL = 'http://mlflow-minio-service.mlflow.svc.cluster.local:9000'


def load_component(filename: str, image_digest: str):
    filepath = COMPONENTS_PATH / filename
    component = components.load_component_from_file(str(filepath))
    component.component_spec.implementation.container.image = f'{IMAGE_URL}@{image_digest}'
    return component


def create_pipeline_func(image_digest: str):
    @dsl.pipeline(name='Training')
    def training_pipeline(bucket_name: str, file_name: str, experiment_name: str):
        pull_data = load_component('pull_data_component.yaml', image_digest)
        pull_data_step = pull_data(bucket_name, file_name)

        preprocess = load_component('preprocess_component.yaml', image_digest)
        preprocess_step: ContainerOp = preprocess(
            input_path=pull_data_step.output
        )

        train = load_component('train_component.yaml', image_digest)
        train_step: ContainerOp = train(
            train_data_dir=preprocess_step.output,
            experiment_name=experiment_name
        )
        train_step.apply(aws.use_aws_secret(secret_name='aws-secret'))
    return training_pipeline


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--image_digest', type=str)
    args = parser.parse_args()

    client = Client(host=None)

    arguments = {
        "bucket_name": BUCKET_NAME,
        "file_name": PROD_DATA_SET,
        "experiment_name": EXPERIMENT_NAME,
    }

    pipeline = create_pipeline_func(image_digest=args.image_digest)

    run = client.create_run_from_pipeline_func(
        pipeline,
        run_name='test_run',
        arguments=arguments,
        experiment_name=EXPERIMENT_NAME,
        mode=PipelineExecutionMode.V2_COMPATIBLE,
        enable_caching=True
    )
