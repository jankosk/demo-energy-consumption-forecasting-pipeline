# Deploy as stand-alone

This deployment uses in-cluster database to persist data.

## Prerequisites

- Storage bucket

## Setup configuration

Update `DEFAULT_ARTIFACT_ROOT` in `config.env` to your bucket location.

## Deploy the stack

Render the deployment:

```bash
# dev/
kubectl kustomize .
```

```bash
# dev/
kubectl apply -k .
```