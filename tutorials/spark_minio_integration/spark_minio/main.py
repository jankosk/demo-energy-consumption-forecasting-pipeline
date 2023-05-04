import kfp
from kfp import dsl
from kfp.v2.dsl import component


@component(
    base_image="127.0.0.1:5001/spark-delta:latest",
    packages_to_install=[],
    output_component_file="components/spark_minio_component.yaml"
)
def read_csv_file_minio(
    s3_endpoint_url: str,
    s3_file_path: str
):
    from pyspark.sql import SparkSession

    SPARK_DRIVE_MEMORY = "4g"
    SPARK_CONNECTION_TIMEOUT = "6000"
    SPARK_MASTER = "local[*]"

    def build_spark_client(
        s3_endpoint_url: str,
        s3_access_key: str,
        s3_secret_key: str,
        spark_app_name: str = "spark-delta",
        spark_master: str = SPARK_MASTER,
        spark_driver_memory: str = SPARK_DRIVE_MEMORY,
        spark_connection_timeout: str = SPARK_CONNECTION_TIMEOUT,
    ) -> SparkSession:
        """Creates a spark client with neccessary configurations for interacting
        with MinIO storage"""

        builder = SparkSession.builder.master(spark_master) \
                .appName(spark_app_name) \
                .config("spark.driver.memory", spark_driver_memory) \
                .config("spark.driver.extraClassPath","/opt/spark/jars/hadoop-aws-3.3.4.jar:/opt/spark/jars/aws-java-sdk-bundle-1.12.389.jar") \
                .config("spark.executor.extraClassPath","/opt/spark/jars/hadoop-aws-3.3.4.jar:/opt/spark/jars/aws-java-sdk-bundle-1.12.389.jar") \
                .config("spark.jars.packages", "io.delta:delta-core_2.12:1.2.1") \
                .config("spark.jars.repositories", "https://maven-central.storage-download.googleapis.com/maven2/") \
                .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
                .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
                .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
                .config("spark.hadoop.fs.s3a.aws.credentials.provider", "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider") \
                .config("spark.hadoop.fs.s3a.endpoint", s3_endpoint_url) \
                .config("spark.hadoop.fs.s3a.access.key", s3_access_key) \
                .config("spark.hadoop.fs.s3a.secret.key", s3_secret_key) \
                .config("spark.hadoop.fs.s3a.connection.timeout", spark_connection_timeout) \
                .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false") \
                .config("spark.hadoop.fs.s3a.path.style.access", "true") \
                .config("spark.delta.logStore.class", "org.apache.spark.sql.delta.storage.S3SingleDriverLogStore")

        return builder.getOrCreate()

    ACCESS_KEY = "minioadmin"
    SECRET_KEY = "minioadmin"

    spark = build_spark_client(
        s3_endpoint_url=s3_endpoint_url,
        s3_access_key=ACCESS_KEY,
        s3_secret_key=SECRET_KEY
    )

    df = spark.read.format("csv") \
        .option("header", True) \
        .option("inferSchema", True) \
        .load(s3_file_path)

    df.show()


@dsl.pipeline(
    name="spark-minio-pipeline",
    description="A demo pipeline to read/write from/to MinIO buckets in Spark"
)
def pipeline(
    s3_endpoint_url: str,
    s3_file_path: str
):
    read_csv_file_minio(s3_endpoint_url, s3_file_path)


if __name__ == "__main__":
    client = kfp.Client(host=None)

    run_name = "spark-minio-run"
    experiment_name = "spark-minio-experiment"

    arguments = {
        "s3_endpoint_url": "http://mlflow-minio-service.mlflow.svc.cluster.local:9000",
        "s3_file_path": "s3a://pyspark-integration/people.csv",
    }

    client.create_run_from_pipeline_func(
        pipeline_func=pipeline,
        run_name=run_name,
        experiment_name=experiment_name,
        arguments=arguments,
        mode=kfp.dsl.PipelineExecutionMode.V2_COMPATIBLE,
        enable_caching=True
    )
