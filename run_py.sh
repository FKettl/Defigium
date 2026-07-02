#!/bin/bash
set -e

# --- CONFIGURATION ---
IMAGE_NAME="python-executor"
CONTAINER_NAME="my-python-run"
SCRIPT_NAME="main.py"  # Replace with your entry script name

# Get absolute paths for volume mounting
PROJECT_DIR=$(pwd)

echo "    Cleaning up any old container instances..."
docker rm -f $CONTAINER_NAME 2>/dev/null || true

echo "    Building Python Docker Image ($IMAGE_NAME)..."
docker build -t $IMAGE_NAME .

echo "    Launching Python Program inside the container..."
# -v mounts your current folder inside the container so logs/outputs persist locally
# --network host allows your script to connect to external databases (like Redis/Postgres) if needed
docker run --rm -it \
    --name $CONTAINER_NAME \
    --network host \
    -v "$PROJECT_DIR:/app" \
    $IMAGE_NAME python $SCRIPT_NAME "$@"

echo "    Execution complete."
