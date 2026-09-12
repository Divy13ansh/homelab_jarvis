# Deployment — cloudflared — What / Why / How

## What

`cloudflared` tunnel `homelab` exposes Gateway via `https://jarvis.divy13ansh.in` without opening homelab ports. Gateway itself binds `127.0.0.1:18789` only.

## Why

CGNAT + client isolation → no public IP/port-forward. Tunnel is outbound 443/TCP, traverses NAT. Safer than exposing Gateway.

## How

### 1. Create tunnel

- Cloudflare Zero Trust → Networks → Tunnels → Create → `homelab` → copy `CLOUDFLARED_TUNNEL_TOKEN` → `.env`
- Or `cloudflared tunnel create homelab` → credentials file → token.

### 2. Public hostname

Zero Trust → Tunnels → `homelab` → Public Hostnames → Add:

- `jarvis.divy13ansh.in` → `http://jarvis:18789` (or `http://127.0.0.1:18789` if cloudflared in same network namespace — compose uses `network_mode: service:jarvis` so `http://127.0.0.1:18789` works)

DNS `jarvis` CNAME auto-created → `*.cfargotunnel.com`.

### 3. Compose

```yaml
services:
  cloudflared:
    image: cloudflare/cloudflared:latest
    command: tunnel run --token ${CLOUDFLARED_TUNNEL_TOKEN}
    depends_on: [jarvis]
    network_mode: service:jarvis
    restart: unless-stopped
```

Gateway must be `bind: loopback` + `auth: token`. Never `bind: lan` with tunnel.

### 4. Cloudflare Access (recommended)

Zero Trust → Access → Applications → Add → `jarvis.divy13ansh.in` → allow `Emails: you@example.com` or `Emails ending in: divy13ansh.in` → plus still require `OPENCLAW_GATEWAY_TOKEN` for API.

### 5. Verify

```bash
docker compose up -d
docker compose logs -f cloudflared  # "Registered tunnel connection"
curl -fsS http://127.0.0.1:18789/healthz
curl -fsS -H "Authorization: Bearer $OPENCLAW_GATEWAY_TOKEN" https://jarvis.divy13ansh.in/healthz
```

### LiveKit Cloud note

Signaling to LiveKit Cloud is direct `wss://xxx.livekit.cloud` (not via tunnel). Tunnel only for Gateway. Media is via Cloud's TURN, not homelab UDP.
