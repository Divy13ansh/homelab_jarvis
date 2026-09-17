#!/bin/bash
set -euo pipefail

PORT="${OPENCLAW_GATEWAY_PORT:-18789}"
CFG_DIR="/home/node/.openclaw"
CFG_FILE="${CFG_DIR}/openclaw.json"
CFG_DIST="${CFG_DIR}/openclaw.json.dist"

mkdir -p "${CFG_DIR}"

if [ ! -f "${CFG_FILE}" ] || ! grep -q '"mode"' "${CFG_FILE}" 2>/dev/null; then
  echo "[entrypoint] seeding ${CFG_FILE} from dist"
  if [ -f "${CFG_DIST}" ]; then
    cp "${CFG_DIST}" "${CFG_FILE}"
  elif [ -f /app/config/openclaw.json ]; then
    cp /app/config/openclaw.json "${CFG_FILE}"
  fi
fi

echo "[entrypoint] ensuring required config options in ${CFG_FILE}"
python3 -c "
import json, pathlib
p = pathlib.Path('${CFG_FILE}')
if p.exists():
    try:
        d = json.loads(p.read_text())
        d.setdefault('gateway', {})['mode'] = 'local'
        d.setdefault('gateway', {}).setdefault('http', {}).setdefault('endpoints', {})['chatCompletions'] = {'enabled': True}
        d.setdefault('agents', {}).setdefault('defaults', {}).setdefault('sandbox', {})['mode'] = 'off'
        p.write_text(json.dumps(d, indent=2))
    except Exception as e:
        print('[entrypoint] config patch error:', e)
"

GATEWAY_ARGS=(gateway --port "${PORT}" --bind lan)

if [ -n "${OPENCLAW_GATEWAY_TOKEN:-}" ]; then
  GATEWAY_ARGS+=(--token "${OPENCLAW_GATEWAY_TOKEN}")
fi

gateway_pid=""
voice_pid=""

term() {
  echo "[entrypoint] SIGTERM received, shutting down"
  [ -n "${voice_pid}" ] && kill -TERM "${voice_pid}" 2>/dev/null || true
  [ -n "${gateway_pid}" ] && kill -TERM "${gateway_pid}" 2>/dev/null || true
  wait || true
  exit 0
}
trap term TERM INT

echo "[entrypoint] starting OpenClaw Gateway on :${PORT}"
node dist/index.js "${GATEWAY_ARGS[@]}" &
gateway_pid=$!

echo "[entrypoint] waiting for Gateway /healthz"
for i in $(seq 1 60); do
  if curl -fsS "http://127.0.0.1:${PORT}/healthz" >/dev/null 2>&1; then
    echo "[entrypoint] Gateway healthy"
    break
  fi
  if ! kill -0 "${gateway_pid}" 2>/dev/null; then
    echo "[entrypoint] Gateway exited unexpectedly" >&2
    wait "${gateway_pid}" || exit 1
  fi
  sleep 1
done

if curl -fsS "http://127.0.0.1:${PORT}/healthz" >/dev/null 2>&1; then
  :
else
  echo "[entrypoint] Gateway failed to become healthy" >&2
  exit 1
fi

if [ -f /app/voice/livekit_agent.py ] && [ -n "${LIVEKIT_URL:-}" ] && [ -n "${LIVEKIT_API_KEY:-}" ]; then
  echo "[entrypoint] ensuring LiveKit model files are present"
  python3 -m livekit.agents download-files 2>/dev/null || true
  echo "[entrypoint] starting LiveKit bridge"
  python3 /app/voice/livekit_agent.py start &
  voice_pid=$!
else
  echo "[entrypoint] LiveKit bridge disabled (missing voice/livekit_agent.py or LIVEKIT_URL/KEY)"
fi

wait "${gateway_pid}"
status=$?
echo "[entrypoint] Gateway exited with ${status}" >&2
[ -n "${voice_pid}" ] && kill -TERM "${voice_pid}" 2>/dev/null || true
exit "${status}"
