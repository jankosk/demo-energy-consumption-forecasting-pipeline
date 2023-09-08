#!/bin/bash

set -e

FILE_NAME=last_run.timestamp

cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: pvc-inspector
  namespace: retraining-job
spec:
  containers:
  - image: busybox
    name: pvc-inspector
    command: ["tail"]
    args: ["-f", "/dev/null"]
    volumeMounts:
    - mountPath: /data
      name: pv
  volumes:
  - name: pv
    persistentVolumeClaim:
      claimName: retraining-pvc
EOF

kubectl -n retraining-job wait --for=condition=ready pod pvc-inspector
echo "Deleting file $FILE_NAME from volume..."
kubectl -n retraining-job exec -it pvc-inspector -- sh -c "rm /data/$FILE_NAME"

kubectl -n retraining-job delete pod pvc-inspector