# Deployment (kustomize)

## 1. Create the cluster

```bash
# /deployment
kind create cluster --name kind-ml --config=cluster/kind-cluster.yaml
```

## 2. Deploy the stack

```bash
# /deployment
kubectl apply -k .
```

## 3. Download `istioctl` and install Istio

Some of kserve components won't be deployed correctly in the previous step (`unable to recognize ".": no matches for kind...`). To complete the kserve installation, download `istioctl` and install Istio with default profile.

```bash
# deployment/
export ISTIO_VERSION=1.11.5
curl -L https://istio.io/downloadIstio | sh -
cd istio-$ISTIO_VERSION
bin/istioctl x precheck
bin/istioctl install --set profile=default -y;
cd ..
rm -rf istio-$ISTIO_VERSION
```

Once installed, re-apply the kustomization to fix the kserve installation:

```bash
# /deployment
kubectl apply -k .
```

Verify the kserve installation:

```bash
$ kubectl get po -n istio-system

NAME                                    READY   STATUS    RESTARTS   AGE
istio-ingressgateway-655cc4bbc6-p7mvx   1/1     Running   0          4m
istiod-5866886d97-2d5fm                 1/1     Running   0          4m16s
```

```bash
$ kubectl get pods -n knative-serving

NAME                                     READY   STATUS    RESTARTS   AGE
activator-68b7698d74-qjv5g               1/1     Running   0          22m
autoscaler-6c8884d6ff-2c262              1/1     Running   0          22m
controller-76cf997d95-26fmz              1/1     Running   0          22m
domain-mapping-57fdbf97b-8xj8w           1/1     Running   0          22m
domainmapping-webhook-66c5f7d596-j7mv2   1/1     Running   0          22m
net-istio-controller-544874485d-4z7kx    1/1     Running   0          22m
net-istio-webhook-695d588d65-ktjrd       1/1     Running   0          22m
webhook-7df8fd847b-jcr99                 1/1     Running   0          22m

```

```bash
$ kubectl --namespace istio-system get service istio-ingressgateway

NAME                   TYPE           CLUSTER-IP      EXTERNAL-IP   PORT(S)                                      AGE
istio-ingressgateway   LoadBalancer   10.96.114.195   <pending>     15021:31336/TCP,80:31947/TCP,443:30097/TCP   5m36s
```
