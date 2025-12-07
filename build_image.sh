#!/usr/bin/env bash
# build_image.sh
# Usage: ./build_image.sh <image-name:tag> <context-dir>

set -euo pipefail

# If no image tag is provided, default to current directory name
DEFAULT_TAG="$(basename "$(pwd)")"
IMAGE_TAG=${1:-$DEFAULT_TAG}
CONTEXT_DIR=${2:-.}
LOGFILE="logs/docker-build-$(date +%Y%m%d-%H%M%S).log"

mkdir -p logs

echo "Starting Docker build for $IMAGE_TAG at $(date)" | tee "$LOGFILE"

# Run build, capture both stdout and stderr
if docker build -t "$IMAGE_TAG" "$CONTEXT_DIR" --debug 2>&1 | tee -a "$LOGFILE"; then
    echo "✅ Build succeeded for $IMAGE_TAG at $(date)" | tee -a "$LOGFILE"
else
    EXIT_CODE=$?
    echo "❌ Build failed for $IMAGE_TAG at $(date) with exit code $EXIT_CODE" | tee -a "$LOGFILE"
fi
read -p "Press Enter to continue..."
