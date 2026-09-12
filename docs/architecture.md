# Architecture — What / Why / How

## What

One disposable `jarvis` container running OpenClaw Gateway + LiveKit bridge, plus `cloudflared` sidecar. LiveKit Cloud handles media/TURN; homelab handles reasoning/tools. Persistent state on host volumes.

## Why

Minimize custom code. OpenClaw owns agent, tools, skills, sessions, channels, sandbox, browser. LiveKit owns realtime media. Docker owns isolation.

## How

```
                 USER
   ┌──────────────┼──────────────┐
 Voice       Discord          (future TG/WA)
   │              │               │
   ▼              └───────┬───────┘
LiveKit Cloud              │
  (SFU+TURN)               │
   │ WSS/STT/TTS           │ message/web_search/browser/exec
   ▼                       ▼
┌─────────────────────────────────┐
│        JARVIS CONTAINER          │
│  ┌───────────────────────────┐  │
│  │ OpenClaw Gateway :18789   │  │
│  │  Tools Skills Sessions    │  │
│  └────────────┬──────────────┘  │
│               │                 │
│     LiveKit Bridge (python)     │
│  voice/livekit_agent.py         │
└───────────────┼─────────────────┘
                │ cloudflared tunnel homelab
                ▼
   https://jarvis.divy13ansh.in
                │
         Docker sandbox (ephemeral, network none)
                │
     /data/projects/*  /data/documents/*  /data/workspace
```

### Container map

- `jarvis` — `ghcr.io/openclaw/openclaw:latest-browser` + `tini` + `entrypoint.sh`, volumes `openclaw-data` + binds, `127.0.0.1:18789`, healthcheck `/healthz`
- `cloudflared` — `network_mode: service:jarvis`, tunnel `homelab`
- `livekit`/`coturn` — only `--profile selfhosted` (fallback)

### Data

```
/mnt/jarvis/  (host)  ↔  container
  openclaw-data → /home/node/.openclaw (config, auth, sessions)
  data/workspace → /workspace
  data/projects → /data/projects/<slug>/{source,artifacts,metadata}
  data/documents → /data/documents/research/*.pdf
  data/logs → /data/logs
```

### Not built

No custom LLM router, memory DB, vector DB, Telegram/Discord/WA clients, browser service, research engine, scheduler, Redis, K8s, microservices.
