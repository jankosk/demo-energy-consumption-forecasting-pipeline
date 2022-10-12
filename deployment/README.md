# Deployment (kustomize)

## Prerequisites

- [curl](https://curl.se/)
- [docker](https://docs.docker.com/engine/install/ubuntu/)
- [kubectl](https://kubernetes.io/docs/tasks/tools/install-kubectl-linux/)
- [kind](https://kind.sigs.k8s.io/docs/user/quick-start/#installation)

## 1. Create the cluster

```bash
# /deployment
kind create cluster --name kind-ep --config=cluster/kind-config.yaml
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