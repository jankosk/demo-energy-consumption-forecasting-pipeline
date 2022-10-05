#!/bin/bash

set -eoa pipefail

#######################################################################################
# DEPLOY KSERVE
#######################################################################################

kubectl apply -k deployment/kserve/cert-manager;

echo "Installing kserve"
# download `istioctl` and install Istio
export ISTIO_VERSION=1.11.5
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
kubectl apply -k deployment/kserve/knative || true;  # allow it fail (race condition might happens)
kubectl apply -k deployment/kserve/knative
kubectl apply -k deployment/kserve/kserve || true;  # allow it fail (race condition might happens)
kubectl apply -k deployment/kserve/kserve

echo Kserve installed!