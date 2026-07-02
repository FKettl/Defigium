set -e

IMAGE_NAME="executor"
CONFIG_FILE="../../config.yaml"
LOGS_PATH="../../logs/"

REAL_CONFIG_PATH=$(realpath "$CONFIG_FILE")
REAL_LOGS_PATH=$(realpath "$LOGS_PATH")

echo "	Building C++ Executor Docker Image..."
docker build -t $IMAGE_NAME .

echo "	Launching C++ Benchmark within the network..."
# Run your application container inside the exact same virtual network
# It can now locate Redis instantly using either the IP or the container name
docker run --rm -it \
	--network host \
    -v "$REAL_CONFIG_PATH:/app/config.yaml" \
    -v "$REAL_LOGS_PATH:/app/logs/" \
    $IMAGE_NAME

echo "	Benchmark complete. Shutting down background Redis container..."
