# Deployment (kustomize)

## 1. Create the cluster

```bash
# /deployment
kind create cluster --name kind-ml --config=cluster/kind-cluster.yaml
```

## 2. Deploy the stack

```bash
# /deployment
kubectl apply -k .
```

## 3. Download `istioctl` and install Istio

Some of kserve components won't be deployed correctly in the previous step (`unable to recognize ".": no matches for kind...`). To complete the kserve installation, download `istioctl` and install Istio with default profile.

```bash
# deployment/
export ISTIO_VERSION=1.11.5
curl -L https://istio.io/downloadIstio | sh -
cd istio-$ISTIO_VERSION
bin/istioctl x precheck
bin/istioctl install --set profile=default -y;
cd ..
rm -rf istio-$ISTIO_VERSION
```

Once installed, re-apply the kustomization to fix the kserve installation:

```bash
# /deployment
kubectl apply -k .
```