#!/bin/bash

set -eou pipefail

function print_help {
  echo "Build the training Docker image and push to image repository"
  echo "Usage: $(basename "$0") [-r IMAGE_REPOSITORY] [-t TAG]"
  echo "options:"
  echo "  -h                      Print this help message and exit"
  echo "  -t=IMAGE_TAG     Push the image to a specified repository instead of the default"
  echo "  -r=IMAGE_REPOSITORY     Push the image to a specified repository instead of the default"
}

IMAGE_REPOSITORY="127.0.0.1:5001"
IMAGE_TAG="latest"

while getopts 'hr:t:' OPT; do
  case "$OPT" in
    h)
      print_help
      exit 0
      ;;
    t)
      IMAGE_TAG=$OPTARG
      ;;
    r)
      IMAGE_REPOSITORY=$OPTARG;
      ;;
    *)
      print_help;
      exit 1
      ;;
  esac
done

IMAGE_NAME=training
IMAGE_FULL_NAME="$IMAGE_NAME:$IMAGE_TAG"
IMAGE_URL="$IMAGE_REPOSITORY/$IMAGE_NAME:$IMAGE_TAG"

echo "Building $IMAGE_FULL_NAME"
docker build -t "$IMAGE_FULL_NAME" .

echo "Pushing image to $IMAGE_URL"
docker tag "$IMAGE_FULL_NAME" "$IMAGE_URL"
docker push "$IMAGE_URL"
