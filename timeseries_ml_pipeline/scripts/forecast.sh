#!/bin/bash

set -eou pipefail

FROM_DATE=$1
if [ -z "$FROM_DATE" ]; then
    echo "Missing datetime argument"
fi

MODEL_NAME=custom-model
ISVC_NAME=test-isvc
INGRESS_GATEWAY_SERVICE=$(kubectl get svc --namespace istio-system --selector="app=istio-ingressgateway" --output jsonpath='{.items[0].metadata.name}')
SERVICE_HOSTNAME=$(kubectl -n kserve-inference get inferenceservice "$ISVC_NAME" -o jsonpath='{.status.url}' | cut -d "/" -f 3)

kubectl port-forward --namespace istio-system svc/"$INGRESS_GATEWAY_SERVICE" 8080:80 &

sleep 1

curl -H "Host: ${SERVICE_HOSTNAME}" http://localhost:8080/v1/models/$MODEL_NAME:predict -d "{\"from_date\": \"${FROM_DATE}\"}"

kill %1

