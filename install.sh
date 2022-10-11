#!/bin/bash

set -eoa pipefail

CLUSTER_NAME="kind-ep"

INSTALL_KSERVE=false
RUN_TESTS=false
LOG_LEVEL_TESTS="WARNING"
while true; do
if [ "$1" = "--kserve" -o "$1" = "-k" ]; then
    INSTALL_KSERVE=true
    shift 1
elif [ "$1" = "--test" -o "$1" = "-t" ]; then
    RUN_TESTS=true
    shift 1
elif [ "$1" = "--debug" -o "$1" = "-d" ]; then
    LOG_LEVEL_TESTS="INFO"
    shift 1
else
    break
fi
done

echo Kserve installation set to: "$INSTALL_KSERVE"
echo Run tests after installation set to: "$RUN_TESTS"

# INSTALL TOOLS
/bin/bash scripts/install_tools.sh

# CREATE CLUSTER
function fail {
    printf "If the previous error is caused because the cluster already exists, you can deleted it with the following command: kind delete cluster --name $CLUSTER_NAME \n" "$1" >&2
    exit "${2-1}" ## Return a code specified by $2, or 1 by default.
}

kind create cluster --name $CLUSTER_NAME --config=deployment/cluster/kind-config.yaml --image=kindest/node:v1.24.0 || fail
kubectl cluster-info --context kind-$CLUSTER_NAME

# DEPLOY STACK
kubectl config use-context kind-$CLUSTER_NAME
kubectl apply -k deployment/  || true # allow to fail -> race condition errors might the first time
kubectl apply -k deployment/  # reapply again to make sure that no errors persist

# DEPLOY KSERVE
if [ $INSTALL_KSERVE == true ]; then
  /bin/bash scripts/install_kserve.sh
fi

echo
echo Installation completed!
echo

# TESTS
if [ "$RUN_TESTS" = "true" ]; then
  /bin/bash scripts/run_tests.sh
fi

exit 0