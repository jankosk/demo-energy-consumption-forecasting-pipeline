#!/bin/bash

set -eoa pipefail

#######################################################################################
# CHECK PRE-REQUISITES
#######################################################################################

# check for docker installation
if ! [[ $(which docker) && $(docker --version) ]]; then
    echo "Docker not found, please install docker. E.g. $ apt install docker.io -y"
    exit 1
fi

#######################################################################################
# INSTALL TOOLS
#######################################################################################

# install curl?
if ! [[ $(which curl) ]]; then
    echo "Curl not found"
    echo "Installing curl"
    sudo apt install curl -y
fi

# install kubectl?
if ! [[ $(which kubectl) ]]; then
    echo "kubectl not found"
    echo "Installing kubectl"
    curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
    sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
    install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
    kubectl version --client
fi

# install Kind?
if ! [[ $(which kind) ]]; then
    echo "kind not found"
    echo "Installing kind"
    curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.14.0/kind-linux-amd64
    chmod +x ./kind
    sudo mv ./kind /usr/local/bin/kind
fi

echo Done!