# Experimentation Platform (IML4E)

MLOps tool stack for the experimentation and training platform.

![](docs/img/iml4e_full.png)

## Project structure

- [`install.sh`](install.sh): Main installation script.
- [`setup.md`](installation.md): Instructions for setting up and testing the platform.
- [`deployment/`](deployment): Kubernetes deployment manifests and configuration (IaC).
- `tutorials/`
  - [`local_deployment/`](tutorials/local_deployment): Developer's guide with step-by-step instructions for local deployment, configuration and testing of
  the different components of the platform.
- [`tests/`](): Test code to verify the deployment.

## Setup

See set up [instructions](setup.md).

### Usage examples

- [Try out MLflow](tutorials/resources/try-mlflow)
- [Try out Kubeflow Pipelines](tutorials/resources/try-kubeflow-pipelines)
- [Try out Kserve](tutorials/resources/try-kserve)

## High-level architecture

![MVP Architecture Diagram](docs/img/iml4e-exp-platform-diagram.png)

### Components

- [Kind](https://kind.sigs.k8s.io/) (cluster setup)
- [Kubernetes](https://kubernetes.io/) (container orchestrator)
- [MLFlow](https://mlflow.org/) (experiment tracking, model registry)
  - [PostgreSQL DB](https://www.postgresql.org/) (metadata store for parameters and metrics)
  - [MinIO](https://min.io/) (artifact store)
- [Kubeflow Pipelines](https://v1-5-branch.kubeflow.org/docs/components/pipelines/introduction/) (ML workflow orchestrator)
- [KServe](https://kserve.github.io/website/0.9/) (model deployment and serving)
- [Prometheus](https://prometheus.io/) (monitoring)
- [Grafana](https://grafana.com/) (monitoring and visualization)

## Support & Feedback

Slack channel [**#iml4e-oss-exp-platform-support**](https://siloai-internal.slack.com/archives/C0463VA0XLP)
can be used for issues, support requests or just discussing feedback. *(Please, send us an email if you would like to be added to the channel)*

Alternatively, feel free to use [Gitlab Issues](https://gitlab.fokus.fraunhofer.de/iml4e/iml4e_oss_exp_platform/-/issues) for bugs, tasks or ideas to be discussed.

Contact people:

- Alari Varmann - alari.varmann@silo.ai
- Joaquin Rives - joaquin.rives@silo.ai

## Contribution guidelines

**TBD**