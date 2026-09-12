# Jarvis — Self-Hosted Personal AI Agent

> OpenClaw does the thinking. LiveKit does the voice. Docker provides isolation. We only connect what can't connect itself.

## What

Personal homelab assistant with voice, messaging (Discord primary), research + document generation, coding sandbox, GitHub project evaluation, and Spotify control — all through one OpenClaw Gateway.

## Why

Minimize custom code. Prefer OpenClaw built-ins → plugin/channel → skill → tiny adapter. Disposable container, persistent state on host.

## How

```
docker compose config
cp .env.example .env   # fill placeholders
docker compose up -d
curl -fsS http://127.0.0.1:18789/healthz
```

See `docs/` for What/Why/How per component.

## Stack

- **Runtime:** Docker + `ghcr.io/openclaw/openclaw:latest-browser`
- **LLM:** Azure OpenAI
- **Voice:** LiveKit Cloud (solves CGNAT/client isolation) + `livekit-agents` bridge
- **Tunnel:** `cloudflared` → `jarvis.divy13ansh.in`
- **Channels:** Discord (`@openclaw/discord`)
- **Music:** Spotify

## Repo Layout

```
jarvis/
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── config/openclaw.json
├── voice/livekit_agent.py
├── skills/{research,project-evaluation,spotify}/SKILL.md
├── scripts/{healthcheck.sh,create_document.py}
└── docs/  # What/Why/How for every component
```
