IMAGE_NAME = 127.0.0.1:5001/training
JOB_NAME = test-job
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

POD=$(shell kubectl -n kserve-inference get pods --sort-by=.metadata.creationTimestamp -o jsonpath='{.items[-1].metadata.name}')
logs:
	kubectl -n kserve-inference logs ${POD} -c kserve-container

JOB=$(shell kubectl -n retraining-job get jobs --sort-by=.metadata.creationTimestamp -o jsonpath='{.items[-1].metadata.name}')
job-logs:
	kubectl -n retraining-job logs job/${JOB}

suspend-job:
	kubectl -n retraining-job patch cronjob/${JOB_NAME} --type=strategic --patch '{"spec":{"suspend":true}}'

run-experiment:
	python -m experiment.simulate_retraining

clear-experiment:
	python -m experiment.set_initial_data
	./scripts/clear_job_data.sh
