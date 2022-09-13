# MLflow on Kubernetes

Customizable [Kustomize](https://kustomize.io/) bases for deploying MLflow on Kubernetes. 

The folder [`base/`](./base) contains an MLflow deployment [base](https://kubernetes.io/docs/tasks/manage-kubernetes-objects/kustomization/#bases-and-overlays) that can be used in overlays.

Overlays available:
- `dev` for deploying MLflow as stand-alone, including in-cluster Postgres database
