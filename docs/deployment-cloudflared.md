# Deployment — cloudflared — What / Why / How

## What

`cloudflared` tunnel `homelab` exposes Gateway via `https://jarvis.divy13ansh.in` without opening homelab ports. Gateway binds `127.0.0.1:18789` only.

## Why

CGNAT + client isolation → no public IP/port-forward. Tunnel is outbound 443/TCP, traverses NAT. Safer than exposing Gateway. Your whole machine is already tunneled, so any service is exposed by adding a hostname.

## How

### Host-wide tunnel (your setup)

Your machine is already running `cloudflared` for the `homelab` tunnel. No sidecar needed in compose.

1. Cloudflare Zero Trust → Networks → Tunnels → `homelab` → Public Hostnames → Add:
   - `jarvis.divy13ansh.in` → `http://127.0.0.1:18789`
2. DNS `jarvis` CNAME auto-creates → `*.cfargotunnel.com`.
3. `docker compose up -d jarvis` — that's it. Add any future port the same way.

### Sidecar mode (portable, not used on this host)

If deploying where host isn't tunneled, add back:

```yaml
services:
  cloudflared:
    image: cloudflare/cloudflared:latest
    command: tunnel run --token ${CLOUDFLARED_TUNNEL_TOKEN}
    depends_on: [jarvis]
    network_mode: service:jarvis
```

### Cloudflare Access (recommended)

Zero Trust → Access → Applications → Add → `jarvis.divy13ansh.in` → allow `Emails: you@divy13ansh.in` → plus still require `OPENCLAW_GATEWAY_TOKEN`.

### Verify

```bash
docker compose up -d jarvis
curl -fsS http://127.0.0.1:18789/healthz
curl -fsS -H "Authorization: Bearer $OPENCLAW_GATEWAY_TOKEN" https://jarvis.divy13ansh.in/healthz
```

### LiveKit Cloud note

Signaling to LiveKit Cloud is direct `wss://xxx.livekit.cloud` (not via tunnel). Tunnel only for Gateway. Media is via Cloud's TURN, not homelab UDP.
