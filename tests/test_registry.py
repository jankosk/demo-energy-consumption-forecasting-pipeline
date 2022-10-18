import subprocess
import logging
import pathlib
import kfp
import pytest
import os
from envsubst import envsubst

from .conftest import HOST_IP
from .test_kfp import _handle_job_end

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BUILD_FILE = pathlib.Path(__file__).parent / "resources" / "registry" / "build_push_image.sh"
PIPELINE_TEMPLATE = pathlib.Path(__file__).parent / "resources" / "registry" / "pipeline.yaml.template"
PIPELINE_FILE = pathlib.Path(__file__).parent / "resources" / "registry" / "pipeline.yaml"

IMAGE_NAME = "kfp-registry-test-image"
EXPERIMENT_NAME = "Test Experiment (Registry)"


def build_push_image():
    logging.info(f"Building and pushing image to local registry...")
    subprocess.run([str(BUILD_FILE), HOST_IP], stdout=True)


def render_pipeline_yaml():
    """Use the pipeline.yaml.template to create the final pipeline.yaml with the
    correct registry IP by replacing the "${HOST_IP}" placeholder."""
    with open(PIPELINE_TEMPLATE, "r") as fr:
        with open(PIPELINE_FILE, "w") as fw:
            fw.write(envsubst(fr.read()))


@pytest.mark.order(7)
@pytest.mark.skipif(
    os.environ.get('INSTALL_LOCAL_REGISTRY') == 'false',
    reason="No local image registry was installed."
)
def test_push_image():
    # build the base docker image and load it into the cluster
    build_push_image()


@pytest.mark.order(8)
@pytest.mark.timeout(120)
@pytest.mark.skipif(
    os.environ.get('INSTALL_LOCAL_REGISTRY') == 'false',
    reason="No local image registry was installed."
)
def test_run_pipeline_using_registry():

    # build the base docker image and load it into the cluster
    build_push_image()

    # create pipeline.yaml with the right registry IP address
    render_pipeline_yaml()

    client = kfp.Client(host=None)

    created_run = client.create_run_from_pipeline_package(
        pipeline_file=str(PIPELINE_FILE),
        enable_caching=False,
        arguments={},
        run_name="kfp_reg_test_run",
        experiment_name=EXPERIMENT_NAME,
    )

    run_id = created_run.run_id

    logger.info(f"Submitted run with ID: {run_id}")

    logger.info(f"Waiting for run {run_id} to complete....")
    run_detail = created_run.wait_for_run_completion()
    _handle_job_end(run_detail)

    experiment = client.get_experiment(experiment_name=EXPERIMENT_NAME)

    client.delete_experiment(experiment.id)
