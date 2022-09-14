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

To access MLFlow UI locally, forward a local port to MinIO server:

```bash
kubectl -n mlflow port-forward svc/mlflow-minio-service 9000:9000
```

Now MLFlow's UI should be reachable at [`http://localhost:9000`](http://localhost:9000).
The default user and password are both `minioadmin`.

> In the [5_Setup_ingress.md](5_Setup_ingress.md) tutorial, we will see how to set up the ingress controller so that we can access
> mlflow and minio without having to use `port-forward`.

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

## Try out MLflow

Follow the instructions of the [MLflow sample](/tutorials/resources/try-mlflow/README.md)
to test the MLflow/MinIO setup.
