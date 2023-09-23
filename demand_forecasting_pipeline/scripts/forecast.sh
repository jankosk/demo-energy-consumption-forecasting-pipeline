#!/bin/bash

set -eou pipefail

FROM_DATE=$1
if [ -z "$FROM_DATE" ]; then
    echo "Missing datetime argument"
fi

MODEL_NAME=demand-forecasting-model
ISVC_NAME=demand-forecasting-isvc
SERVICE_HOSTNAME=$(kubectl -n kserve-inference get inferenceservice "$ISVC_NAME" -o jsonpath='{.status.url}' | cut -d "/" -f 3)

curl -H "Host: ${SERVICE_HOSTNAME}" http://localhost:8080/v1/models/$MODEL_NAME:predict -d "{\"from_date\": \"${FROM_DATE}\"}"