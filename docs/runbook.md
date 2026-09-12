# Runbook — What / Why / How

## What

Operate, health-check, and troubleshoot Jarvis.

## Why

Disposable container must restart cleanly, persist state, and not block voice on long tasks.

## How

### Commands

```bash
docker compose config        # validate
docker compose up -d
docker compose logs -f jarvis
docker compose logs -f cloudflared
curl -fsS http://127.0.0.1:18789/healthz
curl -fsS http://127.0.0.1:18789/readyz
docker compose run --rm jarvis node dist/index.js channels list
docker compose run --rm jarvis node dist/index.js pairing list discord
docker compose restart jarvis
docker compose down && docker compose up -d  # recreate safe, volumes persist
```

### Healthcheck

- Container `HEALTHCHECK` hits `/healthz`; `entrypoint.sh` also waits for it before starting bridge.
- If unhealthy, `cloudflared` still depends_on healthy; restart propagation via `restart: unless-stopped`.

### Voice

- Bridge logs: `docker compose logs -f jarvis | grep jarvis-voice`
- If `LIVEKIT_URL` missing, bridge disabled (Gateway still works).
- Interruptions: `silero VAD` + `MultilingualModel`; test by speaking over Jarvis.

### Long tasks

"Research X and send PDF" → immediate "On it" → background OpenClaw execution → `message` to Discord with file.

### Troubleshooting

| Symptom | Check |
|---------|-------|
| Gateway 401 | `OPENCLAW_GATEWAY_TOKEN` mismatch `.env` vs request |
| Discord offline | `DISCORD_BOT_TOKEN`, intents, `channels list` |
| Research no sources | `browser.enabled` true? image `latest-browser`? |
| PDF fail | `scripts/create_document.py` deps baked; check `/data/documents` perms |
| Sandbox network blocked | expected `network:none`; for `npm install` enable `network:bridge` per eval |
| Tunnel not registered | `CLOUDFLARED_TUNNEL_TOKEN`, Zero Trust hostname `jarvis.divy13ansh.in → http://jarvis:18789` |
| LiveKit no audio | Cloud project keys, Gateway `/v1` reachable, CGNAT requires Cloud (not self-hosted) |

### Secrets rotation

Update `.env`, `docker compose up -d`, re-pair if channel token changed. Never commit `.env`.

### Lint

```bash
ruff check .; mypy .
```
