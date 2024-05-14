.PHONY: build forward-ports kill-ports run-pipeline run-inference isvc-logs retrainer-logs run-experiment clear-experiment

IMAGE_NAME = 127.0.0.1:5001/training
IMAGE_DIGEST = $(shell docker inspect --format='{{index .RepoDigests 0}}' "$(IMAGE_NAME)" | cut -d'@' -f2)

build:
	./scripts/build.sh

forward-ports:
	./scripts/forward_ports.sh

kill-ports:
	./scripts/kill_ports.sh

run-pipeline: build
	python -m pipeline.pipeline --image_digest=$(IMAGE_DIGEST)

FROM_DATE = 2019-04-29T15:00:00
run-inference:
	./scripts/forecast.sh $(FROM_DATE)

ISVC_POD = demand-forecasting-isvc
isvc-logs:
	kubectl -n kserve-inference logs -l app=${ISVC_POD} -c kserve-container -f

RETRAINER_POD = retrainer-pod
retrainer-logs:
	kubectl -n retrainer logs -l app=${RETRAINER_POD} -f

RETRAINER_DEPLOYMENT = retrainer-deployment
kill-retrainer:
	kubectl -n retrainer delete deployment ${RETRAINER_DEPLOYMENT}

run-experiment:
	python -m experiment.simulate_retraining

clear-experiment:
	python -m experiment.set_initial_data
	./scripts/clear_volume.sh
