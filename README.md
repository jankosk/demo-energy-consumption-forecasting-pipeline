# Demo Energy Consumption Forecasting ML Pipeline

Demo implementation of an ML pipeline for forecasting energy consumption of University properties in Finland. The ML pipeline uses a custom error-based retraining trigger to continuously train and serve the model efficiently.

Details: https://helda.helsinki.fi/items/63ff685f-12a0-4c7a-8170-6dd4936f220b

## Local installation
* Follow the instruction in `iml4e_oss_exp_platform` directory to install the MLOps platform
* Add `0.0.0.0 mlflow-server.local mlflow-minio.local ml-pipeline-ui.local` to `/etc/hosts`
* Make sure Python 3.10 is installed
* Create a virtual environment `python3 -m venv env` and activate it `source env/bin/active`
* Install dependencies: `pip install -r requirements.txt`

## Running the pipeline
* Forward ports: `make forward-ports`
* Set initial data: `make set-initial-data`
* Run the pipeline: `make run-pipeline`

## Running the demonstration
* Run the pipeline
* Start demonstration script: `make run-experiment`

## Dashboard
* Access Grafana dashboard at localhost:5000 (requires forwarding ports)
* Import `iml4e_oss_exp_platform/dashboards/energy_consumption_forecasting.json` from the Grafana web UI
* Check the dashboard while running the demonstration to se how the model performs during the experiment
