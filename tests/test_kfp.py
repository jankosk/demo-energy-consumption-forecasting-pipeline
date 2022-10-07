import subprocess
import logging
import pathlib
from dataclasses import dataclass
import kfp
import kfp_server_api
import pytest

from .conftest import CLUSTER_NAME

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BUILD_FILE = pathlib.Path(__file__).parent / "resources" / "kfp" / "build_image.sh"
PIPELINE_FILE = pathlib.Path(__file__).parent / "resources" / "kfp" / "pipeline.yaml"

IMAGE_NAME = "kfp-test-img"
EXPERIMENT_NAME = "Test Experiment"


def _handle_job_end(run_detail: kfp_server_api.ApiRunDetail):
    finished_run = run_detail.to_dict()["run"]

    created_at = finished_run["created_at"]
    finished_at = finished_run["finished_at"]

    duration_secs = (finished_at - created_at).total_seconds()

    status = finished_run["status"]

    logger.info(f"Run finished in {round(duration_secs)} seconds with status: {status}")

    if status != "Succeeded":
        raise Exception(f"Run failed: {run_detail.run.id}")


def build_load_image():
    output = subprocess.check_output(
        ["docker", "exec", f"{CLUSTER_NAME}-control-plane", "crictl", "images"]
    )

    if IMAGE_NAME in output.decode():
        logging.info(f"Image already in cluster.")
    else:
        logging.info(f"Image not found in cluster. Building and loading image...")
        subprocess.run([str(BUILD_FILE)], stdout=True)


@pytest.mark.order(6)
@pytest.mark.timeout(120)
def test_run_pipeline():

    # Build the base docker image and load it into the cluster
    build_load_image()

    client = kfp.Client(host=None)

    created_run = client.create_run_from_pipeline_package(
        pipeline_file=str(PIPELINE_FILE),
        enable_caching=False,
        arguments={},
        run_name="kfp_test_run",
        experiment_name=EXPERIMENT_NAME,
    )

    run_id = created_run.run_id

    logger.info(f"Submitted run with ID: {run_id}")

    logger.info(f"Waiting for run {run_id} to complete....")
    run_detail = created_run.wait_for_run_completion()
    _handle_job_end(run_detail)

    experiment = client.get_experiment(experiment_name=EXPERIMENT_NAME)

    client.delete_experiment(experiment.id)
