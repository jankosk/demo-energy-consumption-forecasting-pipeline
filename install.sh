#!/bin/bash

set -eoa pipefail

source config.env

RUN_TESTS=false
LOG_LEVEL_TESTS="WARNING"

while true; do
if [ "$1" = "--test" -o "$1" = "-t" ]; then
    RUN_TESTS=true
    shift 1
elif [ "$1" = "--debug" -o "$1" = "-d" ]; then
    LOG_LEVEL_TESTS="INFO"
    shift 1
else
    break
fi
done

echo Cluster name set to: "$CLUSTER_NAME"
echo Host IP set to: "$HOST_IP"
echo Kserve installation set to: "$INSTALL_KSERVE"
echo Run tests after installation set to: "$RUN_TESTS"

# INSTALL TOOLS
/bin/bash scripts/install_tools.sh

# CREATE CLUSTER
function fail {
    printf "If the previous error is caused because the cluster already exists, you can deleted it with the following command: kind delete cluster --name $CLUSTER_NAME \n" "$1" >&2
    exit "${2-1}" ## Return a code specified by $2, or 1 by default.
}

/bin/bash scripts/create_cluster.sh || fail

kubectl cluster-info --context kind-$CLUSTER_NAME

# DEPLOY LOCAL DOCKER REGISTRY
if [ $INSTALL_LOCAL_REGISTRY == true ]; then
  /bin/bash scripts/install_local_registry.sh
fi

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