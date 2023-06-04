IMAGE_NAME = 127.0.0.1:5001/training
IMAGE_DIGEST = $(shell docker inspect --format='{{index .RepoDigests 0}}' "$(IMAGE_NAME)" | cut -d'@' -f2)

build:
	./build.sh

run: build
	python -m pipeline.pipeline --image_digest=$(IMAGE_DIGEST)
