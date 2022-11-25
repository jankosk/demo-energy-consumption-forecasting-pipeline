### Setup RBAC user access

This is used to grant the user group `users` fine-grained access to resources in the cluster using kubernetes role-based access control (RBAC).

These RBAC manifests grant the following permissions to the group `users`:

- Enough permissions to deploy, delete, etc. inference services in the `kserve-inference` namespace: [`kserve-inference-access.yaml`](kserve-inference-access.yaml)
- View services in the `istio-system` namespace in order to access the ingress gateway of the inference services: : [`istio-system-access.yaml`](istio-system-access.yaml)
