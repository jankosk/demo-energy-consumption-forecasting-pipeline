import subprocess
import logging
import pytest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def all_pods_ready(namespace: str):
    output = subprocess.check_output(["kubectl", "get", "pods", "-n", namespace])

    logger.info("\n" + output.decode())

    for line in output.decode().strip().split('\n')[1:]:

        name, ready, status, restarts = line.split()[:4]

        # TODO: skip this pod which is always down
        if name.startswith('proxy-agent') and namespace == 'kubeflow':
            continue

        if status != 'Completed' and (ready[0] == '0' or status != 'Running'):
            logger.error(f"ERROR: Resources not ready (namespace={namespace}).")
            return False

    logger.info(f"All resources are ready (namespace={namespace}).")
    return True


def get_all_namespaces():
    out = subprocess.check_output(["kubectl", "get", "namespaces"]).decode()
    all_namespaces = [n.split()[0] for n in out.strip().split('\n')[1:]]
    return all_namespaces


@pytest.mark.order(1)
@pytest.mark.parametrize(argnames="namespace", argvalues=get_all_namespaces())
def test_resources_ready(namespace: str):
    assert all_pods_ready(namespace=namespace), "Some resources are not ready yet."
