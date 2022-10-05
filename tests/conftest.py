import subprocess

CLUSTER_NAME = "kind-ep"
CONTEXT_NAME = "kind-kind-ep"

AWS_ACCESS_KEY_ID = 'minioadmin'
AWS_SECRET_ACCESS_KEY = 'minioadmin'


def pytest_sessionstart(session):
    """
    Called after the Session object has been created and
    before performing collection and entering the run test loop.
    """
    print(f"Set up kubectl context ({CONTEXT_NAME}) before starting the tests.")

    subprocess.run(["kubectl", "config", "use-context", CONTEXT_NAME], stdout=True)
