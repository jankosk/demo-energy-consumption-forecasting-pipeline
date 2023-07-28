# Sample Kubeflow component and pipeline

This is a sample of a Kubeflow Pipeline component and pipeline adapted from [here](https://github.com/kubeflow/pipelines/tree/sdk/release-1.8/components/sample/keras/train_classifier).

The purpose is to show how to create a simple pipeline component and run a KFP pipeline.
By default, the example uses a local Kind cluster (`kind-ep`) and the local docker repository. Modify the files appropriately for your own environment if needed.

This example uses custom containers for components. You may also want to learn about [building Python function-based components](https://www.kubeflow.org/docs/components/pipelines/sdk-v2/python-function-components/) as an alternative approach.

This example uses [Pipelines SDK v2](https://www.kubeflow.org/docs/components/pipelines/sdk-v2/).

## Pre-requisites

Ensure your `kubectl` has correct context pointing to the desired cluster. For example, for the `kind-ep` cluster:

```bash
kubectl config use-context kind-kind-ep
```

## Push container image

The file [`train.py`](./train.py) contains sample for model training. MLflow is used for experiment tracking.

The file [`Dockerfile`](./Dockerfile) contains the commands to assemble a Docker image for training.

Image is built [`build_image.sh`](./build_image.sh). Read through the script. By default, images are loaded into the local cluster directly from the local docker repository using the `kind load docker-image` command.

Build and load the image into the cluster:

```bash
./build_image.sh
```

## Create component

Kubeflow pipeline component for training is defined in [`component.yaml`](./component.yaml). See the documentation on [component specification](https://www.kubeflow.org/docs/components/pipelines/reference/component-spec/) to understand how components are defined. In brief, every component has 

- metadata such as name and description
- implementation specifying how to execute the component instance: Docker image, command and arguments
- interface specifying the inputs and outputs

Update the container image under `implementation.container.image` so that it matches the image pushed with `build_image.sh`.

## Create pipeline

The file [`pipeline.py`](./pipeline.py) contains the definition for the Kubeflow pipeline:

```python
# pipeline.py
import kfp

# Load component from YAML file
train_op = kfp.components.load_component_from_file('component.yaml')

@kfp.dsl.pipeline(name='Example Kubeflow pipeline', description='Pipeline to test an example component')
def pipeline():
    train_task = train_op()

def compile():
    kfp.compiler.Compiler().compile(
        pipeline_func=pipeline,
        package_path='pipeline.yaml'
    )

if __name__ == '__main__':
    compile()
```

Compile the pipeline to `pipeline.yaml`:

```bash
python pipeline.py
```

Submit pipeline run to Kubeflow Pipelines:

```bash
kfp run submit -f pipeline.yaml -e "Test experiment"
```

You can also submit the pipeline file manually in Kubeflow Pipelines UI.

## Dashboards

To visit the Kubeflow Pipelines UI, forward a local port with:

```bash
kubectl port-forward -n kubeflow svc/ml-pipeline-ui 8080:80
```

Then access the pipeline UI at [http://localhost:8080/](http://localhost:8080/).

To access MLFlow UI, forward a local port to MLFlow server with:

```bash
kubectl -n mlflow port-forward svc/mlflow 5000:5000
```

Then access the MLflow UI at [`http://localhost:5000`](http://localhost:5000).
