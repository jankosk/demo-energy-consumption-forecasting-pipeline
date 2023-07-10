IMAGE_NAME = 127.0.0.1:5001/training
IMAGE_DIGEST = $(shell docker inspect --format='{{index .RepoDigests 0}}' "$(IMAGE_NAME)" | cut -d'@' -f2)

build:
	./scripts/build.sh

run-pipeline: build
	python -m pipeline.pipeline --image_digest=$(IMAGE_DIGEST)

run-inference:
	./scripts/forecast.sh

POD=$(shell kubectl -n kserve-inference get pods --sort-by=.metadata.creationTimestamp -o jsonpath='{.items[-1].metadata.name}')
logs:
	kubectl -n kserve-inference logs ${POD} -c kserve-container

