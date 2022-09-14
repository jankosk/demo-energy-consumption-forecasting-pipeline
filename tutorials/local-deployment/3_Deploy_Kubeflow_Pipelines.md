<h1> Deploy Kubeflow Pipelines (KFP) </h1>

[TOC]

## Pre-requisites

- [1_Setup_local_cluster.md](1_Setup_local_cluster.md)

## 1. Prepare `kubectl` context

Check your current context in `kubectl` and make sure it is pointing to the target cluster we created in the previous tutorial (`kind-kind-ml`). 

```bash
# check current context
kubectl config current-context
```

Switch `kubectl` to the right context by modifying the variables if necessary:

```bash
kubectl config use-context kind-kind-ml
```

You can also list all the available contexts with:

```bash
# list all contexts
kubectl config get-contexts
```

## 2. Install Kubeflow Pipelines

Perform a [`standalone deployment`](https://www.kubeflow.org/docs/components/pipelines/installation/standalone-deployment/#deploying-kubeflow-pipelines)
of Kubeflow Pipelines:

```bash
export PIPELINE_VERSION=1.8.4
kubectl apply -k "github.com/kubeflow/pipelines/manifests/kustomize/cluster-scoped-resources?ref=$PIPELINE_VERSION"
kubectl wait --for condition=established --timeout=60s crd/applications.app.k8s.io
kubectl apply -k "github.com/kubeflow/pipelines/manifests/kustomize/env/dev?ref=$PIPELINE_VERSION"
```

Deployment will take a few minutes. You can check the status with:

```bash
kubectl get pods -n kubeflow
```

After the deployment as completed, the UI can be accessed using port forwarding:

```bash
kubectl port-forward -n kubeflow svc/ml-pipeline-ui 8080:80
```

Then access the pipeline UI at [http://localhost:8080/](http://localhost:8080/).


## 3. Create KFP ingress

Create an ingress for the KFP UI:

```bash
kubectl apply -f deployment/kfp/kfp-ingress.yaml
```

## 4. Run example pipelines

In the UI, navigate to `pipelines` from the sidebar. Click any of the example pipelines and click `Create run` button to test out the examples. 

If the pipelines succeed, the pipeline installation had succeeded.

> Skip the **TFX - Taxi tip prediction model trainer** pipeline, as it needs access to a storage bucket. We will set up access the Google Cloud resources in the next sections.

## 5. Build your first pipeline

Follow the [KFP sample tutorial](../resources/try-kubeflow-pipelines/README.md) to learn how to build a simple KFP pipeline and/or test the kind+KFP+MLflow setup from end-to-end. 