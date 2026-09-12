# Voice — LiveKit — What / Why / How

## What

Realtime voice via LiveKit Agents + OpenClaw Gateway. `voice/livekit_agent.py` is a tiny bridge (join room → STT → Gateway LLM → TTS). No reasoning/memory/tools in bridge.

## Why

LiveKit handles WebRTC, STT/TTS streaming, VAD/turn detection, interruptions. OpenClaw handles reasoning/tools/memory. Bridge only connects them. LiveKit **Cloud** solves CGNAT/client isolation where homelab can't expose UDP.

## How

### LiveKit Cloud (primary — CGNAT)

You are behind CGNAT + client isolation → homelab cannot expose UDP 50000-60000 or TURN publicly. Cloud's SFU+TURN is reachable via outbound 443/TCP, no port-forward needed. 10k min free is ample for personal Jarvis.

1. https://cloud.livekit.io → create project → copy `LIVEKIT_URL=wss://xxx.livekit.cloud`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET` → `.env`
2. `voice/livekit_agent.py` uses `openai.LLM(base_url=http://jarvis:18789/v1, api_key=OPENCLAW_GATEWAY_TOKEN)` to forward STT text to OpenClaw Gateway's OpenAI-compat `/v1/chat/completions`. Gateway does all agent work.
3. Session mapping: `LiveKit room → OpenClaw session` via gateway; conversation persists across turns in same room.
4. Latency: streaming STT/TTS, `preemptive_generation=True`, interrupt handling via `vad=silero.VAD` + `MultilingualModel` turn detector.

### Self-hosted fallback (profile)

If you later get public IP/VPS:

```bash
docker compose --profile selfhosted up -d livekit coturn
```

- `config/livekit.yaml` (mount) + `config/turnserver.conf` with `static-auth-secret=${TURN_SHARED_SECRET}`, `external-ip=<public IP>`, `use_external_ip: true`.
- Point `LIVEKIT_URL=wss://livekit.divy13ansh.in` (needs TURN TLS 5349 + UDP range open).
- Cloudflared cannot carry UDP — media must be direct.

### Run

```bash
# homelab
pip install -r voice/requirements.txt  # or bake in image
LIVEKIT_URL=wss://xxx.livekit.cloud LIVEKIT_API_KEY=... LIVEKIT_API_SECRET=... \
OPENCLAW_GATEWAY_URL=http://127.0.0.1:18789/v1 OPENCLAW_GATEWAY_TOKEN=... \
python3 voice/livekit_agent.py dev   # or start via entrypoint.sh

# container (entrypoint.sh starts gateway then bridge if LIVEKIT_URL present)
docker compose up -d jarvis
docker compose logs -f jarvis
```

### Bridge responsibilities (only)

- Join room, RX audio → STT, TX TTS, interruptions, turn detection
- Forward LLM calls to Gateway (no local LLM logic)
- NOT: memory, tools, research, coding — all OpenClaw

### Verification

- Join LiveKit room → speak → Jarvis replies via TTS → interrupt mid-sentence → handled
- Long task: "Research X and send report" → immediate "On it" → background task → delivery via Discord
