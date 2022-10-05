

## Installation

Install the experimentation platform with:

```bash
./install.sh [--test] [--debug]
```
- `--test`: Use this flag to run the tests right after installation.
- `--debug`: Print extra output information.

> **WARNING:** Using the `--test` flag will install the `requirements-tests.txt` in your default python environment.

## Test the deployment (manually)

If you just deployed the platform, it will take a while to become ready. You can use
the following script to make sure the deployment is ready and all resource are running
correctly.

```bash
python tests/wait_deployment_ready.py --timeout 30
```

Run the tests with:

```bash
# install test requirements
pip install -r tests/requirements-tests.txt
# run tests
pytest [-vrP] [--log-cli-level=INFO]
```

*These are the same tests that are run automatically if you use the `--test` flag on installation.*


## Deleting the deployment

```bash
kind delete cluster --name kind-ep
```
