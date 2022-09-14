# Sklearn inference service

This directory contains an example of an inference service (kserve) using a sklearn model.

See [sklearn-iris-model.yaml](sklearn-iris-model.yaml).

## Deploy the model inference service

```bash
# tutorials/resources/try-kserve
kubectl apply -k .
```

Check that the inference service was deployed correctly:

```bash
$ kubectl get inferenceservice -n kserve-inference

NAME           URL                                                READY   PREV   LATEST   PREVROLLEDOUTREVISION   LATESTREADYREVISION                    AGE
sklearn-iris   http://sklearn-iris.kserve-inference.example.com   True           100                              sklearn-iris-predictor-default-00001   48m
```

> It might take a few minutes to become "READY".

## Try a prediction request

Determine the name of the ingress gateway to the inference service:

```bash
INGRESS_GATEWAY_SERVICE=$(kubectl get svc --namespace istio-system --selector="app=istio-ingressgateway" --output jsonpath='{.items[0].metadata.name}')

echo $INGRESS_GATEWAY_SERVICE
```

Port Forward to the ingress gateway service:

```bash
kubectl port-forward --namespace istio-system svc/${INGRESS_GATEWAY_SERVICE} 8080:80
```

Start another terminal and set the following variables

```bash
export MODEL_NAME=sklearn-iris
export INGRESS_HOST=localhost
export INGRESS_PORT=8080
export SERVICE_HOSTNAME=$(kubectl -n kserve-inference get inferenceservice $MODEL_NAME -o jsonpath='{.status.url}' | cut -d "/" -f 3)

echo $SERVICE_HOSTNAME
```

Send a prediction request:

```bash
# tutorials/resources/try-kserve
curl -H "Host: ${SERVICE_HOSTNAME}" http://localhost:8080/v1/models/$MODEL_NAME:predict -d @./iris-input.json
```
