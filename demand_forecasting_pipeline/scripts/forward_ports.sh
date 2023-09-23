#!/bin/bash

set -eou pipefail

INGRESS_GATEWAY_SERVICE=$(kubectl get svc --namespace istio-system --selector="app=istio-ingressgateway" --output jsonpath='{.items[0].metadata.name}')

kubectl port-forward -n istio-system svc/"$INGRESS_GATEWAY_SERVICE" 8080:80 & \

kubectl port-forward -n mlflow svc/mlflow-minio-service 9000:9000 & \
kubectl port-forward -n mlflow svc/mlflow-minio-service 9001:9001 & \
