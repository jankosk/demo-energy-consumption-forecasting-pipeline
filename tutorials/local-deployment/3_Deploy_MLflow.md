<h1> Deploy MLflow </h1>

In this guide, we deploy [MLflow](https://mlflow.org/) tracking server to Kubernetes.

[MLflow](https://mlflow.org/) is an open source platform to manage the ML lifecycle, including experimentation, reproducibility, deployment, and a central model registry.

The deployment uses [MinIO](https://min.io/) as artifact store as a location for large data and training artifacts (for example, models).
MinIO is a High Performance Object Storage native to Kubernetes and API compatible with Amazon S3 cloud storage service.

MLflow also requires an SQL database as backend store. This deployment uses an in-cluster PostgreSQL database for that purpose.

[TOC]

## Pre-requisites

- [1_Setup_local_cluster.md](1_Setup_local_cluster.md)


## Understand Kustomize

Kubernetes' resources are deployed using [Kustomize](https://kustomize.io/).
See [this presentation](https://docs.google.com/presentation/d/1-j7ux5-P9HcftKlXM9KHKgrG0EgwwGEKE3f01Sp0oes/edit?usp=sharing)
and [this tutorial](https://kubernetes.io/docs/tasks/manage-kubernetes-objects/kustomization/)
to understand the basics.

## MLflow Docker image

Dockerfile use to build the docker image for MLflow can be found [`here`](/docker/mlflow).

## Deploy MLFlow

The folder [`deployment/mlflow`](/deployment/mlflow) contains a [Kustomize](https://kubernetes.io/docs/tasks/manage-kubernetes-objects/kustomization/) [overlay](https://kubernetes.io/docs/tasks/manage-kubernetes-objects/kustomization/#bases-and-overlays)
that can be used for deploying MLFlow.

Print Kubernetes resources that you would deploy:

```bash
# deployment/
kubectl kustomize mlflow
```

Deploy the stack:

```bash
# Deploy from `deployment/` folder
kubectl apply -k mlflow
```

## Check deployment health

Wait until pods labeled as `mlflow` and `postgres` become ready:

```bash
kubectl -n mlflow wait --for=condition=ready pod -l app=mlflow
kubectl -n mlflow wait --for=condition=ready pod -l app=postgres
kubectl -n mlflow wait --for=condition=ready pod -l app=mlflow-minio
```

See the pods running in `mlflow` namespace. All pods should be ready and running.

```bash
$ kubectl -n mlflow get pods
mlflow-7b7c7b6d68-mflj4         1/1     Running   0          13m
mlflow-minio-674cb5cc55-hlkrq   1/1     Running   0          3h32m
postgres-547474dc58-8fscf       1/1     Running   0          3h37m
```

If anything is wrong, you can read the pod logs with:

```bash
kubectl -n mlflow logs -l app=mlflow
```

## Access MLflow UI

To access MLFlow UI locally, forward a local port to MLFlow server:

```bash
kubectl -n mlflow port-forward svc/mlflow 5000:5000
```

Now MLFlow's UI should be reachable at [`http://localhost:5000`](http://localhost:5000).

## Access Minio UI

To access MLFlow UI locally, forward a local port to MLFlow server:

```bash
kubectl -n mlflow port-forward svc/mlflow-minio-service 9000:9000
```

Now MLFlow's UI should be reachable at [`http://localhost:9000`](http://localhost:9000).

> In next tutorial, we will see how to set up the ingress controller so that we can access
> mlflow and minio without using `port-forward`.

## Create MinIO bucket

We deployed [MinIO](https://min.io/) alongside MLflow, however, we still need to create
the bucket that we are going to use as artifact store. It must have the same name as indicated in the
`DEFAULT_ARTIFACT_ROOT` variable in [config.env](mlflow/dev/config.env).

### Option 1: Manually

Access the UI and create and create the bucket manually.

You can do it by clicking the plus sign in the bottom right of the UI, selecting
“Create New Bucket”, and naming your new bucket “mlflow”.

### Option 2: Using MinIO client

First make sure MinIO is accessible by using port-forwarding:

```bash
kubectl -n mlflow port-forward svc/mlflow-minio-service 9000:9000
```

Then, install [MinIO client for linux](https://docs.min.io/docs/minio-client-quickstart-guide.html)
and use it to create the bucket.

```bash
# install minio client
wget https://dl.min.io/client/mc/release/linux-amd64/mc
chmod +x mc
sudo mv ./mc /usr/local/bin/mc
mc --help

# configure access to the server
mc alias set minio-kind 'http://localhost:9000/' minioadmin minioadmin

# create bucket
mc mb minio-kind/mlflow

# check that the bucket was created succesfully
mc ls minio-kind
```

## Test MLFlow deployment

First, make sure mlflow and minio server are both, MLflow ([http://localhost:5000](http://localhost:5000))
and Minio ([http://localhost:9000](http://localhost:9000)), are accessible:

MLflow:
```bash
kubectl -n mlflow port-forward svc/mlflow 5000:5000
```

MinIO:
```bash
kubectl -n mlflow port-forward svc/mlflow-minio-service 9000:9000
```

### Create an experiment run

Create a new working directory and a virtual environment with your method of choice.

Install dependencies:

```bash
pip install mlflow google-cloud-storage scikit-learn
```

Create a sample Python file named `train.py` adapted from [train.py](https://github.com/mlflow/mlflow/blob/master/examples/sklearn_elasticnet_wine/train.py) used in the [MLflow tutorial](https://www.mlflow.org/docs/latest/tutorials-and-examples/tutorial.html):

```python
# train.py
# Adapted from https://github.com/mlflow/mlflow/blob/master/examples/sklearn_elasticnet_wine/train.py
import logging
import sys

import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.linear_model import ElasticNet
import os

os.environ['MLFLOW_S3_ENDPOINT_URL'] = 'http://localhost:9000/'
os.environ['AWS_ACCESS_KEY_ID'] = 'minioadmin' 
os.environ['AWS_SECRET_ACCESS_KEY'] = 'minioadmin'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MLFLOW_TRACKING_URI = "http://localhost:5000"
MLFLOW_EXPERIMENT_NAME = "mlflow-minio-test"


def eval_metrics(actual, pred):
    rmse = np.sqrt(mean_squared_error(actual, pred))
    mae = mean_absolute_error(actual, pred)
    r2 = r2_score(actual, pred)
    return rmse, mae, r2


def main():
    np.random.seed(40)

    # Read the wine-quality csv file from the URL
    csv_url = (
        "http://archive.ics.uci.edu/ml/machine-learning-databases/wine-quality/winequality-red.csv"
    )

    data = pd.read_csv(csv_url, sep=";")

    # Split the data into training and test sets. (0.75, 0.25) split.
    train, test = train_test_split(data)

    # The predicted column is "quality" which is a scalar from [3, 9]
    train_x = train.drop(["quality"], axis=1)
    test_x = test.drop(["quality"], axis=1)
    train_y = train[["quality"]]
    test_y = test[["quality"]]

    alpha = float(sys.argv[1]) if len(sys.argv) > 1 else 0.5
    l1_ratio = float(sys.argv[2]) if len(sys.argv) > 2 else 0.5

    logger.info(f"Using MLflow tracking URI: {MLFLOW_TRACKING_URI}")
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

    logger.info(f"Using MLflow experiment: {MLFLOW_EXPERIMENT_NAME}")
    mlflow.set_experiment(MLFLOW_EXPERIMENT_NAME)

    with mlflow.start_run():
        lr = ElasticNet(alpha=alpha, l1_ratio=l1_ratio, random_state=42)

        logger.info("Fitting model...")

        lr.fit(train_x, train_y)

        logger.info("Finished fitting")

        predicted_qualities = lr.predict(test_x)

        (rmse, mae, r2) = eval_metrics(test_y, predicted_qualities)

        logger.info("Elasticnet model (alpha=%f, l1_ratio=%f):" % (alpha, l1_ratio))
        logger.info("  RMSE: %s" % rmse)
        logger.info("  MAE: %s" % mae)
        logger.info("  R2: %s" % r2)

        logger.info("Logging parameters to MLflow")
        mlflow.log_param("alpha", alpha)
        mlflow.log_param("l1_ratio", l1_ratio)
        mlflow.log_metric("rmse", rmse)
        mlflow.log_metric("r2", r2)
        mlflow.log_metric("mae", mae)

        logger.info("Logging trained model")
        mlflow.sklearn.log_model(lr, "model", registered_model_name="ElasticnetWineModel")

if __name__ == '__main__':
    main()

```

Run the script:

```bash
python train.py
```

After the script finishes, navigate to the MLflow UI at [http://localhost:5000](http://localhost:5000),
and you should see your run under the experiment "mlflow-minio-test". Browse the run parameters, metrics and artifacts.
