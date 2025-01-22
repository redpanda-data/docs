#!/bin/bash

WORK_DIR="$(pwd)"

# Function to check if Docker containers are running
function check_docker_containers {
  if docker compose ps | grep -q "Up"; then
    docker compose down --volumes
  fi
}

# Check and delete the "redpanda-quickstart" folder for replayability
if [ -d "redpanda-quickstart" ]; then
  rm -rf redpanda-quickstart
fi

# Create folder and set up Redpanda quickstart
echo "Setting up redpanda-quickstart folder..."
mkdir redpanda-quickstart && cd redpanda-quickstart || exit 1
curl -sSL https://deploy-preview-937--redpanda-docs-preview.netlify.app/redpanda-quickstart.tar.gz | tar xzf -
cd docker-compose/three-brokers || exit 1

# Check and handle Docker containers
check_docker_containers
docker compose up -d

# Navigate back to the initial working directory
cd "$WORK_DIR" || {
  echo "Failed to navigate back to the working directory: $WORK_DIR. Exiting."
  exit 1
}

# Check and install Python3
if ! command -v python3 &>/dev/null; then
  echo "Python3 not found. Installing Python3..."
  if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    sudo apt update && sudo apt install -y python3
  elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    echo "Please install Python3 manually from https://www.python.org/downloads/"
    exit 1
  fi
fi

# Check and install pip
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
  echo "Running metrics.py..."
  python3 "$WORK_DIR/metrics.py"
else
  echo "metrics.py not found in $WORK_DIR. Please ensure it exists."
fi
