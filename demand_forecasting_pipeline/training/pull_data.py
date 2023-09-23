import argparse
from pathlib import Path
from minio import Minio
from shared import config


def pull_data(bucket_name: str, file_name: str, output_path: Path):
    minio_client = Minio(
        endpoint=config.S3_MINIO_ENDPOINT,
        access_key=config.MINIO_ACCESS_KEY,
        secret_key=config.MINIO_SECRET_KEY,
        secure=False
    )

    found = minio_client.bucket_exists(bucket_name)
    if not found:
        raise Exception(f"Bucket {bucket_name} does not exist")

    minio_client.fget_object(
        bucket_name=bucket_name,
        object_name=file_name,
        file_path=str(output_path)
    )


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--bucket_name', type=str)
    parser.add_argument('--file_name', type=str)
    parser.add_argument('--output_path', type=Path,
                        default='./data/training.csv')
    args = parser.parse_args()

    pull_data(bucket_name=args.bucket_name,
              file_name=args.file_name, output_path=args.output_path)
