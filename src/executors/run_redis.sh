set -e

LOGS_PATH="../../logs/"
REDIS_NAME="my-redis-server"
REDIS_PORT="7000"
REDIS_LOGGER="redis-logger"

REAL_LOGS_PATH=$(realpath "$LOGS_PATH")

echo "	Cleaning up any old containers or networks..."
docker rm -f $REDIS_NAME 2>/dev/null || true
docker rm -f $REDIS_LOGGER 2>/dev/null || true

echo "	Starting Redis on Port: $REDIS_PORT..."
# We tell Redis internally to bind to all interfaces on port 6379 inside the container,
# but we map it to our specific custom IP and port on the bridge network.
docker run --name $REDIS_NAME -d \
    -p $REDIS_PORT:6379 \
    redis redis-server --port 6379 --bind 0.0.0.0

sleep 1.5

docker run --name $REDIS_LOGGER --rm \
	--network container:$REDIS_NAME \
	redis redis-cli -p 6379 MONITOR > "$REAL_LOGS_PATH/monitor/redis_output.log" 2>&1 &

echo "	Listenning for the load on port $REDIS_PORT"
