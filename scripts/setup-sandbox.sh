#!/bin/bash
set -euo pipefail
if docker image inspect openclaw-sandbox:bookworm-slim >/dev/null 2>&1; then
  echo "openclaw-sandbox:bookworm-slim already exists"
  exit 0
fi
cat > /tmp/Dockerfile.sandbox <<'DOCKER'
FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends python3 python3-pip tini curl git && rm -rf /var/lib/apt/lists/* && useradd -m -s /bin/bash agent
WORKDIR /workspace
DOCKER
docker build -f /tmp/Dockerfile.sandbox -t openclaw-sandbox:bookworm-slim /tmp
