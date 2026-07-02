#!/bin/bash
set -e

# Validate input configurations before executing
if [ "$#" -ne 2 ]; then
    echo "❌ Execution Error: Missing parameters."
    echo "👉 Usage: $0 <REDIS_NODE_IP> <REDIS_NODE_PORT>"
    echo "💡 Example: $0 192.168.1.50 7000"
    exit 1
fi

REDIS_IP="$1"
REDIS_PORT="$2"
RESULTS_DIR="./ycsb_results"

mkdir -p "$RESULTS_DIR"
REAL_RESULTS_PATH=$(realpath "$RESULTS_DIR")

echo "🏗️  Assembling multi-dependency YCSB Docker Context..."
cat << 'EOF' > Dockerfile.ycsb
FROM eclipse-temurin:11-jdk-focal

RUN apt-get update && apt-get install -y \
    git \
    python3 \
    maven \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN ln -s /usr/bin/python3 /usr/bin/python
WORKDIR /app
RUN git clone https://github.com/brianfrankcooper/YCSB.git
WORKDIR /app/YCSB
RUN mvn -pl site.ycsb:redis-binding -am clean package -DskipTests

ENTRYPOINT ["./bin/ycsb"]
EOF

echo "📦 Building the runtime benchmark image..."
docker build -f Dockerfile.ycsb -t ycsb-executor .
rm Dockerfile.ycsb

echo "📥 Executing Phase 1: Data Insertion (Loading 10,000 records)..."
# `--network host` maps the container to the machine network space to bypass internal routing barriers
docker run --rm \
    --network host \
    ycsb-executor load redis \
    -P workloads/workloada \
    -p redis.host="$REDIS_IP" \
    -p redis.port="$REDIS_PORT" \
    > "$RESULTS_DIR/load.log"

echo "📊 Executing Phase 2: Simulating Workload A (50/50 Read-Update Split)..."
docker run --rm \
    --network host \
    ycsb-executor load redis \
	-s \
    -P workloads/workloada \
     > "$RESULTS_DIR/load.log"

docker run --rm \
    --network host \
	ycsb-executor run redis \
	-s \
	-P workloads/workloada \
	> "$RESULTS_DIR/run.log"

echo "------------------------------------------------------------------"
echo "✅ Benchmark execution sequence complete!"
echo "📈 Throughput and latencies saved inside: $RESULTS_DIR/run.log"
echo "------------------------------------------------------------------"
