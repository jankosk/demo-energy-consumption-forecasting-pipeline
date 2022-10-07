import subprocess
from tempfile import TemporaryDirectory
from pathlib import Path
import time
import pytest
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

USERNAME = "TestUser"
GROUP = "users"

CREATE_USER_PATH = Path(__file__).parent / "resources" / "access_management" / "create_user"
MLFOW_PERMISSIONS = Path(__file__).parent / "resources" / "access_management" / "user_permissions" / "mlflow_permissions.txt"
KUBEFLOW_PERMISSIONS = Path(__file__).parent / "resources" / "access_management" / "user_permissions" / "kubeflow_permissions.txt"

NAMESPACES = ["default", "ingress-nginx", "kube-node-lease", "kube-public", "kube-system", "kubeflow", "local-path-storage", "mlflow"]


@pytest.fixture(scope="module", autouse=True)
def kube_config():
    """ Creates a new user in the cluster for testing and removes it afterwards.
    Returns: user kubeconfig for impersonating the created test user.
    """
    print("setup")
    try:
        with TemporaryDirectory() as tmp_dir:
            out = subprocess.check_output(
                [
                    str(CREATE_USER_PATH / "create_user.sh"),
                    "-u",
                    USERNAME,
                    "-g",
                    GROUP,
                    "-o",
                    tmp_dir,
                ],
            )
            logger.info("\n" + out.decode())

            time.sleep(5)

            yield str(Path(tmp_dir)/f"{USERNAME}-kubeconfig")
    finally:
        print("teardown")
        out = subprocess.check_output(["kubectl", "delete", "csr", f"{USERNAME}-csr"])
        logger.info("\n" + out.decode())


def test_cluster_access(kube_config: str):
    out = subprocess.check_output(["kubectl", "version", "--kubeconfig", kube_config])
    logger.info("\n" + out.decode())


def test_kubeflow_access(kube_config: str):
    permissions = subprocess.check_output(
        [
            "kubectl",
            "auth",
            "can-i",
            "--list",
            "-n",
            "kubeflow",
            "--kubeconfig",
            kube_config
        ]
    ).decode()

    with open(KUBEFLOW_PERMISSIONS, "r") as f:
        kubeflow_permissions = f.read()

        assert permissions == kubeflow_permissions


def test_mlflow_access(kube_config: str):
    permissions = subprocess.check_output(
        [
            "kubectl",
            "auth",
            "can-i",
            "--list",
            "-n",
            "mlflow",
            "--kubeconfig",
            kube_config
        ]
    ).decode()

    with open(MLFOW_PERMISSIONS, "r") as f:
        mlflow_permissions = f.read()

        assert permissions == mlflow_permissions


@pytest.mark.parametrize(argnames="namespace", argvalues=NAMESPACES)
def test_no_access(kube_config: str, namespace: str):
    exit_code = None
    out = None
    verb = 'delete'
    try:
        _ = subprocess.check_output(
            [
                "kubectl",
                "auth",
                "can-i",
                verb,
                "pods",
                "-n",
                namespace,
                "--kubeconfig",
                kube_config,
            ]
        )
    except subprocess.CalledProcessError as grepexc:
        exit_code = grepexc.returncode
        out = grepexc.output.decode().strip()

    logger.info(f"\n{namespace} access: {out} - Exit code: {exit_code}")

    assert exit_code == 1 and out == "no", \
        f"User shouldn't have delete permission on {namespace} namespace."
