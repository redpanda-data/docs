#!/bin/bash

# Usage:
#   ./extract_metrics.sh [redpanda_tag] [redpanda_docker_repo] [redpanda_console_tag] [redpanda_console_docker_repo]

REDPANDA_TAG="${1:-latest}"

REDPANDA_DOCKER_REPO="${2:-redpanda}"

REDPANDA_CONSOLE_TAG="${3:-latest}"

REDPANDA_CONSOLE_DOCKER_REPO="${4:-console}"

# Export the values so they're accessible to the Docker Compose
export REDPANDA_VERSION="$REDPANDA_TAG"
export REDPANDA_DOCKER_REPO="$REDPANDA_DOCKER_REPO"
export REDPANDA_CONSOLE_VERSION="$REDPANDA_CONSOLE_TAG"
export REDPANDA_CONSOLE_DOCKER_REPO="$REDPANDA_CONSOLE_DOCKER_REPO"

REDPANDA_MAJOR_MINOR=$(echo "$TAG" | sed -E 's/^v?([0-9]+\.[0-9]+).*$/\1/')

WORK_DIR="$(pwd)"

# Function to check if Docker containers are running
function check_docker_containers {
  if docker compose ps | grep -q "Up"; then
    docker compose down --volumes
  fi
}

if [ -d "docker-compose" ]; then
  cd docker-compose || exit 1
else
  echo "Setting up redpanda-quickstart folder..."
  curl -sSL https://docs.redpanda.com/$REDPANDA_MAJOR_MINOR-redpanda-quickstart.tar.gz | tar xzf -
  cd docker-compose || exit 1
fi

# Check and handle Docker containers
check_docker_containers
docker compose up -d

echo "Waiting 120 seconds for Redpanda to start..."
sleep 120

cd "$WORK_DIR" || {
  echo "Failed to navigate back to the working directory: $WORK_DIR. Exiting."
  exit 1
}

# Check and install Python3 if needed
if ! command -v python3 &>/dev/null; then
  echo "Python3 not found. Installing Python3..."
  if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    sudo apt update && sudo apt install -y python3
  elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    echo "Please install Python3 manually from https://www.python.org/downloads/"
    exit 1
  fi
fi

# Check and install pip if needed
if ! command -v pip3 &>/dev/null; then
  echo "pip not found. Installing pip..."
  python3 -m ensurepip --upgrade || sudo apt install -y python3-pip
fi

# Install required Python libraries
if [ -f "$WORK_DIR/requirements.txt" ]; then
  echo "Installing required Python libraries from requirements.txt..."
  pip3 install -q -r "$WORK_DIR/requirements.txt"
else
  echo "requirements.txt not found in $WORK_DIR. Please ensure it exists."
fi

# Run the metrics.py script
if [ -f "$WORK_DIR/metrics.py" ]; then
  echo "Running metrics.py with TAG=$TAG..."
  python3 "$WORK_DIR/metrics.py" "$TAG"
else
  echo "metrics.py not found in $WORK_DIR. Please ensure it exists."
fi

# Tear down Docker containers after the script has run
echo "Tearing down Docker containers..."
cd docker-compose || {
  echo "Failed to navigate to docker-compose directory. Exiting.";
  exit 1;
}
docker compose down --volumes
