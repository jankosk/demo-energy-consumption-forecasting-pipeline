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

## 3. Deploy kserve

### Download `istioctl` and install Istio

```bash
# deployment/
export ISTIO_VERSION=1.11.5
curl -L https://istio.io/downloadIstio | sh -
cd istio-$ISTIO_VERSION
bin/istioctl x precheck
bin/istioctl install --set profile=default -y;
# reinstall again in case of timeout error
bin/istioctl install --set profile=default -y;
cd ..
rm -rf istio-$ISTIO_VERSION
```

```bash
# /deployment
kubectl apply -k kserve/
```