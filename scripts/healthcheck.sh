#!/bin/sh
set -eu
PORT="${OPENCLAW_GATEWAY_PORT:-18789}"
curl -fsS "http://127.0.0.1:${PORT}/healthz" >/dev/null 2>&1
