#!/usr/bin/env bash
set -euo pipefail

# File: run_test_env.sh
# Purpose: build and run the docker-compose.test.yml in detached mode and show how to exec into it

CONTAINER_NAME="hunter_debug"

# Build and start the service in the background (detached)
docker compose -f docker-compose.test.yml up -d --build

# Show status and useful commands
echo "Started containers (detached)."
echo "View logs: docker compose -f \"docker-compose.test.yml\" logs -f"
echo "Open an interactive shell inside the running container:"
echo "  docker exec -it $CONTAINER_NAME /bin/bash"
echo "If /bin/bash is unavailable, try /bin/sh:"
echo "  docker exec -it $CONTAINER_NAME /bin/sh"