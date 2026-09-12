# Configuration — What / Why / How

## What

Env-driven config with secrets in `.env` (gitignored), OpenClaw JSON with `${VAR}` / SecretRef, and compose variable substitution.

## Why

Container disposable; state persists in volumes. No secrets in repo, Dockerfile, or logs.

## How

### `.env`

```bash
cp .env.example .env
# fill AZURE_OPENAI_ENDPOINT/KEY/DEPLOYMENT/API_VERSION
# fill OPENCLAW_GATEWAY_TOKEN (openssl rand -hex 32)
# fill DISCORD_BOT_TOKEN
# fill LIVEKIT_URL/KEY/SECRET
# fill SPOTIFY_CLIENT_ID/SECRET
# fill CLOUDFLARED_TUNNEL_TOKEN
```

### `config/openclaw.json`

```json5
{
  gateway: { port: 18789, bind: "loopback", auth: { mode: "token", token: { source: "env", id: "OPENCLAW_GATEWAY_TOKEN" } } },
  models: { providers: { azure: { apiKey: { source: "env", id: "AZURE_OPENAI_API_KEY" }, baseUrl: "${AZURE_OPENAI_ENDPOINT}", apiVersion: "${AZURE_OPENAI_API_VERSION}" } } },
  agents: { defaults: { model: "azure/${AZURE_OPENAI_DEPLOYMENT}" } },
  tools: { web: { search: { enabled: true }, fetch: { enabled: true } }, browser: { enabled: true } },
  channels: { discord: { enabled: true, token: { source: "env", id: "DISCORD_BOT_TOKEN" }, dmPolicy: "pairing" } }
}
```

### `docker-compose.yml`

- `OPENCLAW_IMAGE` arg defaults `ghcr.io/openclaw/openclaw:latest-browser` (per your choice).
- Gateway binds `127.0.0.1:18789`, not public; cloudflared tunnels.
- Volumes: `openclaw-data:/home/node/.openclaw` + bind mounts `./data/{workspace,projects,documents,logs}`.
- Docker socket `/var/run/docker.sock` enables OpenClaw sandbox backend when enabled.

### Adding a channel/tool

Prefer plugin/channel → skill → tiny adapter. Do not duplicate OpenClaw built-ins (`message`, `web_search`, `browser`, `exec`).

### Verify

```bash
docker compose config  # expand vars, check no blank secrets
docker compose up -d
curl -fsS http://127.0.0.1:18789/healthz
curl -fsS http://127.0.0.1:18789/readyz
```
