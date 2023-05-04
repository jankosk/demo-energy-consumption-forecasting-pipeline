#!/bin/bash

set -xeoa pipefail

#######################################################################################
# DEPLOY KSERVE
#######################################################################################

kubectl apply -k deployment/kserve/cert-manager;

# download `istioctl` and install Istio
echo "Installing istioctl"

if [[ -n "$(docker info --format '{{.OperatingSystem}}' | grep 'Docker Desktop')" ]]; then
    echo "You seem to be running Docker Desktop"
    echo "Make sure to increase Docker resource limit to at least 4 CPUs and 8GB of memory "
    echo "before installing Istio!"
    echo
fi

export ISTIO_VERSION=1.16.0
curl -L https://istio.io/downloadIstio | sh -
cd istio-$ISTIO_VERSION
bin/istioctl x precheck;
bin/istioctl install --set profile=default -y || true;  # allow it fail as it sometimes times out
# the previous command sometimes times out, wait for istiod and istio-ingressgateway
# to become ready and reinstall again just in case
kubectl -n istio-system wait --for=condition=ready pod -l app=istiod --timeout 15m
kubectl -n istio-system wait --for=condition=ready pod -l app=istio-ingressgateway --timeout 15m
bin/istioctl install --set profile=default -y;
cd ..
rm -rf istio-$ISTIO_VERSION

# deploy kserve
echo "Installing kserve"
kubectl apply -k deployment/kserve/knative || true;  # allow it fail (race condition might happens)
kubectl apply -k deployment/kserve/knative
kubectl apply -k deployment/kserve/kserve || true;  # allow it fail (race condition might happens)
kubectl apply -k deployment/kserve/kserve

echo Kserve installed!

exit 0