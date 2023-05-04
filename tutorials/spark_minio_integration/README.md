# Spark-MinIO integration

This short tutorial demos how to read/write from/to MinIO bucket in Spark.

## Prepare:
In your local MinIO deployment, create a package called `pyspark-integration` and upload the `data/people.csv` file to that package

## How to run:

**Step 1:** 
Build the docker image inside `docker/spark-delta` with:
```
cd docker/spark-delta && ./build.sh -p latest
```
This will build the docker image with proper libraries and setup for Spark and push it to the local registery.

**Step 2:**
Run the `spark_minio/main.py` as
```
python -m spark_minio.main
```

## Code deep-dive:
The helper function `build_spark_client` builds a Spark session with proper configurations to connect and work with MinIO.