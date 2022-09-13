# Deploy KServe

In this section, we deploy [KServe](https://kserve.github.io/website/0.8/), scalable model inference platform on Kubernetes.

## Pre-requisites

- [Preparation](./01_Preparation.md)
- [Create GCP resources](./02_Create_GCP_Resources.md)
- [`curl`](https://curl.se/)
- [`wget`](https://www.gnu.org/software/wget/)

## Deployment

> The latest installation instructions can be found [here](https://kserve.github.io/website/master/admin/serverless/).

We need to install:

- [Istio](https://istio.io/) with the [`default`](https://istio.io/latest/docs/setup/additional-setup/config-profiles/) profile
- [Knative Serving](https://knative.dev/docs/): Serving component and Istio network layer component
- [Cert Manager](https://cert-manager.io/docs/)
- [KServe](https://kserve.github.io/website/)

### Define versions

Refer to the installation matrix to understand which versions of tools to install. Check your Kubernetes server version with:

```bash
kubectl version
```

Add the version variables suitable for your environment. For example, to install [KServe 0.8.0](https://kserve.github.io/website/0.8/admin/serverless/) on Kubernetes 1.21:

```bash
export KSERVE_VERSION=0.8.0
export CERTMANAGER_VERSION=1.8.0
export KNATIVE_VERSION=1.0.0
export ISTIO_VERSION=1.11.5
```

Ensure that your kubecontext is correct:

```bash
kubectl config current-context
```

### Deploy Cert Manager

> See the [installation guide](https://cert-manager.io/docs/installation/) for latest installation instructions.

Ensure `CERTMANAGER_VERSION` is defined:

```bash
echo $CERTMANAGER_VERSION
```

Fetch the manifest and apply:

```bash
# deployment/
mkdir cert-manager
wget https://github.com/cert-manager/cert-manager/releases/download/v$CERTMANAGER_VERSION/cert-manager.yaml -O cert-manager/cert-manager.yaml
```

Apply:

```bash
kubectl apply -f cert-manager
```

### Install Istio

> See the [installation guide](https://istio.io/latest/docs/setup/install/) for alternative installation methods.

Ensure `ISTIO_VERSION` is defined:

```bash
echo $ISTIO_VERSION
```

Download `istioctl` and install Istio with default profile:

```bash
# deployment/
curl -L https://istio.io/downloadIstio | sh -
cd istio-$ISTIO_VERSION
bin/istioctl x precheck
bin/istioctl install --set profile=default -y;
cd ..
rm -rf istio-$ISTIO_VERSION
```

### Install KNative Serving

> See the [installation guide](https://knative.dev/docs/install/) for alternative installation methods.

Ensure `KNATIVE_VERSION` is defined:

```bash
echo $KNATIVE_VERSION
```

Fetch manifests:

```bash
# deployment/
mkdir knative
wget https://github.com/knative/serving/releases/download/knative-v$KNATIVE_VERSION/serving-crds.yaml -O knative/serving-crds.yaml
wget https://github.com/knative/serving/releases/download/knative-v$KNATIVE_VERSION/serving-core.yaml -O knative/serving-core.yaml
```

Apply the resources:

```bash
# deployment/
kubectl apply -f knative/serving-crds.yaml
kubectl apply -f knative/serving-core.yaml
kubectl wait --for=condition=ready --timeout=600s pods --all -n knative-serving
```

Fetch and install KNative Istio controller:

```bash
# deployment/
wget https://github.com/knative-sandbox/net-istio/releases/download/knative-v$KNATIVE_VERSION/net-istio.yaml -O knative/net-istio.yaml
kubectl apply -f knative/net-istio.yaml
```

Verify that all pods are running:

```bash
kubectl get pods -n knative-serving
```

### Install KServe

The latest documentation can be found in [serverless installation guide](https://kserve.github.io/website/master/admin/serverless/).

Install KServe:

```bash
# deployment/
mkdir kserve
wget https://github.com/kserve/kserve/releases/download/v${KSERVE_VERSION}/kserve.yaml -O kserve/kserve.yaml
kubectl apply -f kserve/kserve.yaml
```

Install KServe runtimes:

```bash
# deployment/
wget https://github.com/kserve/kserve/releases/download/v${KSERVE_VERSION}/kserve-runtimes.yaml -O kserve/kserve-runtimes.yaml
kubectl apply -f kserve/kserve-runtimes.yaml
```

Verify pods are running:

```bash
kubectl get pods -n kserve
```

Test the service by following the instructions [here](https://kserve.github.io/website/master/get_started/first_isvc/#run-your-first-inferenceservice).
