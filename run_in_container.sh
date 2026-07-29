#!/usr/bin/env bash
set -e

# Automatically detect user container engine 
if command -v podman &> /dev/null; then
    ENGINE="podman"
    # NOTE: Podman on Linux needs ':z' for SELinux volume security contexts
    VOL_SUFFIX=":z"
    # Streamline image name selection by using localhost/
    IMAGE="localhost/seismogram-pipeline"
else
    ENGINE="docker"
    VOL_SUFFIX=""
    IMAGE="seismogram-pipeline"
fi

# Uncomment to mannually select the engine 
# ENGINE="docker"
# VOL_SUFFIX=""
# IMAGE="seismogram-pipeline"

echo "==> Using container engine: $ENGINE"

# Ensure data directories exist locally to avoid permission issues
mkdir -p data/inputs data/outputs

# Run the container using the detected engine
$ENGINE run --rm \
  -v "$(pwd)/data/inputs:/app/data/inputs$VOL_SUFFIX" \
  -v "$(pwd)/data/outputs:/app/data/outputs$VOL_SUFFIX" \
  "$IMAGE" "$@"

# Example usage:
# ./run_in_container.sh --image /app/data/inputs/COL_75_06_16_1706_LHZ.png --output /app/data/outputs/ --scale 0.25
# ./run_in_container.sh seismogram-get-roi --image /app/data/inputs/COL_75_06_16_1706_LHZ.png --output /app/data/outputs/roi.json --scale 0.25
