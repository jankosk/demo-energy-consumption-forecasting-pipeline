<h1> Set up a local kubernetes cluster with Kind </h1>

Set up a local kubernetes cluster with [Kind](https://kind.sigs.k8s.io/).

[TOC]

### 1. Install kubectl

```bash
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
kubectl version --client
```

### 2. Install Kind:

```bash
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.14.0/kind-linux-amd64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind
```

### 3. Create a cluster

```bash
kind create cluster --name kind-ml --config=deployment/cluster/kind-cluster.yaml
```

The config [`kind-cluster.yaml`](/deployment/cluster/kind-cluster.yaml) contains the
configuration needed for setting up the ports and enable the ingress later on.

### 4. (Optional) Setup Kubernetes dashboard UI

[Setup Kubernetes dashboard UI](https://istio.io/latest/docs/setup/platform-setup/kind/#setup-dashboard-ui-for-kind) for browsing Kubernetes resources. See also the [official documentation](https://kubernetes.io/docs/tasks/access-application-cluster/web-ui-dashboard/.)
