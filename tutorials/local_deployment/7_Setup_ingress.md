<h1> Setup ingress </h1>

When deploying KFP and MLflow in the previous tutorials, we also created ingresses for
accessing their UIs without having to use `port-forward`.

In this tutorial we will see how to get the ingresses working. We will use NGINX to
route to these services.

## 1. Deploy Ingress controller (NGINX)

NGINX is a free, open-source, high-performance HTTP server and reverse proxy.

```bash
# /deployment
mkdir nginx
wget https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml -O nginx/nginx-kind-deployment.yaml
kubectl apply -f nginx/nginx-kind-deployment.yaml
```

The manifests contain kind specific patches to forward the hostPorts to the ingress
controller, set taint tolerations and schedule it to the custom labelled node.

## 2. Update hosts

Map the cluster IP to the host names in your `/etc/hosts` file.

Open your `/etc/hosts` file. E.g.
```bash
sudo nano /etc/hosts
```

Append the following line with the IP of the cluster and save the changes.

```
0.0.0.0 mlflow-server.local mlflow-minio.local ml-pipeline-ui.local
```

> To access the ingresses from another computer in the local network, replace `0.0.0.0`
> with the real IP of the computer running the cluster. 

Now the ingress is all setup. You should be able to access these services by simple
navigating on your browser to their addresses:

- KFP UI: [http://ml-pipeline-ui.local](http://ml-pipeline-ui.local)
- MLflow UI: [http://mlflow-server.local](http://mlflow-server.local)
- MinIO (MLflow) UI: [http://mlflow-minio.local](http://mlflow-minio.local)
