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
kind create cluster --name kind-ep --config=deployment/cluster/kind-config.yaml --image=kindest/node:v1.24.0
```

The config [`kind-config.yaml`](../../deployment/cluster/kind-config.yaml) contains the
configuration needed for setting up the ports and enable the ingress later on.

The default IP address (`127.0.0.1`) is only accessible from the computer the cluster is running on.
If you want to make your cluster accessible from other computer in the local network,
change the `apiServerAddress:` field to the real IP address of the computer.

You can get the IP by running:

```bash
# get computer IP in LAN
ip -o route get to 8.8.8.8 | sed -n 's/.*src \([0-9.]\+\).*/\1/p'

# or alternatively
hostname -I | cut -d' ' -f1
```
