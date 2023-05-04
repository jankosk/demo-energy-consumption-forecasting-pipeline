#!/bin/bash

set -xeoa pipefail

#######################################################################################
# Create and configure a cluster with Kind
#
# Usage: $ export HOST_IP=127.0.0.1; export CLUSTER_NAME="kind-ep"; ./create_cluster.sh
#######################################################################################


if [ "$INSTALL_LOCAL_REGISTRY" = "true" ]; then
# create a cluster with the local registry enabled in containerd
cat <<EOF | kind create cluster --name $CLUSTER_NAME --image=kindest/node:v1.24.0 --config=-
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
networking:
  ipFamily: dual
  apiServerAddress: ${HOST_IP}
nodes:
- role: control-plane
  kubeadmConfigPatches:
  - |
    kind: InitConfiguration
    nodeRegistration:
      kubeletExtraArgs:
        node-labels: "ingress-ready=true"
  extraPortMappings:
  - containerPort: 80
    hostPort: 80
    protocol: TCP
  - containerPort: 443
    hostPort: 443
    protocol: TCP
containerdConfigPatches:
- |-
  [plugins."io.containerd.grpc.v1.cri".registry.mirrors."${HOST_IP}:5001"]
    endpoint = ["http://kind-registry:5000"]
EOF

else
# create a cluster
cat <<EOF | kind create cluster --name $CLUSTER_NAME --image=kindest/node:v1.24.0 --config=-
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
networking:
  ipFamily: dual
  apiServerAddress: ${HOST_IP}
nodes:
- role: control-plane
  kubeadmConfigPatches:
  - |
    kind: InitConfiguration
    nodeRegistration:
      kubeletExtraArgs:
        node-labels: "ingress-ready=true"
  extraPortMappings:
  - containerPort: 80
    hostPort: 80
    protocol: TCP
  - containerPort: 443
    hostPort: 443
    protocol: TCP
EOF

fi

exit 0