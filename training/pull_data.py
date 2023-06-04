import argparse
import os
from pathlib import Path
from minio import Minio

S3_MINIO_ENDPOINT = os.getenv(
    'S3_MINIO_ENDPOINT', 'mlflow-minio-service.mlflow.svc.cluster.local:9000')
ACCESS_KEY = os.getenv('ACCESS_KEY', 'minioadmin')
SECRET_KEY = os.getenv('SECRET_KEY', 'minioadmin')


def pull_data(bucket_name: str, file_name: str, output_path: Path):
    minio_client = Minio(
        endpoint=S3_MINIO_ENDPOINT,
        access_key=ACCESS_KEY,
        secret_key=SECRET_KEY,
        secure=False
    )

    found = minio_client.bucket_exists(bucket_name)
    if not found:
        raise Exception(f"Bucket {bucket_name} does not exist")

    minio_client.fget_object(
        bucket_name=bucket_name,
        object_name=file_name,
        file_path=output_path
    )


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--bucket_name', type=str)
    parser.add_argument('--file_name', type=str)
    parser.add_argument('--output_path', type=Path,
                        default='./data/training.csv')
    args = parser.parse_args()

    pull_data(bucket_name=args.bucket_name, file_name=args.file_name, output_path=args.output_path)
