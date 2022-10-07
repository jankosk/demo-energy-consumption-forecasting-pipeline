### Setup RBAC user access

This is used to grant the user group `users` fine-grained access to resources in the cluster using kubernetes role-based access control (RBAC).

These RBAC manifests grant the following permissions to the group `users`:

- View pods/services, proxy and port-forward access in the `kubeflow` namespace: [`kubeflow-access.yaml`](kubeflow-access.yaml)
- View pods/services and port-forward access in the `mlflow` namespace: [`mlflow-access.yaml`](mlflow-access.yaml)