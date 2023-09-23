from minio import Minio
from minio.deleteobjects import DeleteObject
from shared import config
from pathlib import Path


def upload():
    minio_client = Minio(
        endpoint='localhost:9000',
        access_key='minioadmin',
        secret_key='minioadmin',
        secure=False
    )
    errors = minio_client.remove_objects(
        config.BUCKET_NAME,
        [
            DeleteObject(config.PREDICTIONS_DATA),
            DeleteObject(config.PROD_DATA)
        ]
    )
    for error in errors:
        print('Error occured when deleting object', error)

    file = 'initial_data.csv'
    minio_client.fput_object(
        config.BUCKET_NAME,
        config.PROD_DATA,
        Path(__file__).parent / file
    )
    print(f'Uploaded {file} to Minio')


if __name__ == '__main__':
    upload()
