# MLflow on Kubernetes

Customizable [Kustomize](https://kustomize.io/) bases for deploying MLflow on Kubernetes. 

This is a stand-alone MLflow deployment, including in-cluster Postgres database and MinIO as artifact storage.

## Setup configuration

Update `DEFAULT_ARTIFACT_ROOT` in `default.env` to your bucket location.

Replace the default secrets in [`secret.env`](secret.env) with your own.
