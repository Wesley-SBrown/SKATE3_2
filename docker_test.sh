#!/usr/bin/env bash
set -e

# Ensure data directories exist locally to avoid permission issues
mkdir -p data/inputs data/outputs

# Run the seismogram pipeline container, mounting local data
docker run --rm \
  -v "$(pwd)/data/inputs:/app/data/inputs" \
  -v "$(pwd)/data/outputs:/app/data/outputs" \
  seismogram-pipeline "$@"

# Example usage:
# ./docker_test.sh --image /app/data/inputs/COL_75_06_16_1706_LHZ.png --output /app/data/outputs/ --scale 0.25