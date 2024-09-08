#!/bin/bash

set -e

FILE_NAME=last_run.timestamp

cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: pvc-inspector
  namespace: retrainer
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
      claimName: retrainer-pvc
EOF

kubectl -n retrainer wait --for=condition=ready pod pvc-inspector
echo "Deleting file $FILE_NAME from volume..."
kubectl -n retrainer exec -it pvc-inspector -- sh -c "rm /data/$FILE_NAME"

kubectl -n retrainer delete pod pvc-inspector