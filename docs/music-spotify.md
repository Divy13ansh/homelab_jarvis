# Music — Spotify — What / Why / How

## What

Tiny adapter `voice/spotify_adapter.py` over Spotify Web API, driven by `skills/spotify/SKILL.md`.

## Why

No OpenClaw built-in music streaming; we use hierarchy level 4 (tiny adapter), not a service. Adapter only wraps search/play/queue/pause/next/volume.

## How

### 1. Create Spotify app

1. https://developer.spotify.com/dashboard → Create App → name `Jarvis`, redirect URI `http://127.0.0.1:8888/callback` (must match `SPOTIFY_REDIRECT_URI` in `.env`)
2. Copy Client ID/Secret → `.env` `SPOTIFY_CLIENT_ID/SECRET`
3. Add scopes on first auth are handled by adapter: `user-read-playback-state user-modify-playback-state user-read-currently-playing`

### 2. Authenticate

```bash
docker exec -it jarvis-jarvis-1 python3 /app/voice/spotify_adapter.py auth
# Preferred: the running container already publishes 127.0.0.1:8888, so auth
# runs in place. Do NOT use `docker compose run -p 8888:8888 …` while jarvis
# is up — the host port is already allocated and the run container fails to
# create. (If jarvis is stopped, that form works as a fallback. There is no
# --env-file flag on `run`; the service loads .env via `env_file:` anyway.)
# opens browser → authorize → callback to 127.0.0.1:8888 → saves /home/node/.openclaw/spotify.json (refresh token)
# token auto-refreshes on each call
```

For headless homelab, run `auth` via SSH with port forward or `ssh -L 8888:127.0.0.1:8888 homelab`.

### 3. Use

```bash
python3 /app/voice/spotify_adapter.py search --query "Radiohead Creep"
python3 /app/voice/spotify_adapter.py play --query "Radiohead Creep"
python3 /app/voice/spotify_adapter.py play --query "Lo-fi beats" --device "Living Room"
python3 /app/voice/spotify_adapter.py pause
python3 /app/voice/spotify_adapter.py next
python3 /app/voice/spotify_adapter.py volume --value 50
python3 /app/voice/spotify_adapter.py status
python3 /app/voice/spotify_adapter.py queue --uri spotify:track:xxx
```

### 4. Jarvis natural language

```
User (Discord/Voice): Jarvis, play some Radiohead
Jarvis: spotify_adapter play --query "Radiohead" → "Playing Radiohead — Creep on Living Room"
```

### Troubleshooting

- **No active device:** Open Spotify on a device first (phone/speaker). Adapter can target by `--device`.
- **Token expired:** adapter refreshes via `refresh_token`; if `spotify.json` deleted, re-run `auth`.
- **Premium required:** playback control requires Spotify Premium.
- **`not authenticated. run: ... auth`:** token file `/home/node/.openclaw/spotify.json` missing. Run the `auth` command above; the `127.0.0.1:8888:8888` port mapping in compose must be live (`docker port jarvis-jarvis-1` should list it) or the OAuth callback never arrives.
- **Redirect URI mismatch:** Spotify dashboard app redirect URI must exactly equal `SPOTIFY_REDIRECT_URI` (`http://127.0.0.1:8888/callback`). Recheck for trailing slashes.
- **Skill not loading:** `skills/spotify/SKILL.md` must exist on host; compose mounts `./skills` to `/home/node/.openclaw/skills` and `/workspace/skills`. Verify with `docker exec jarvis-jarvis-1 ls /home/node/.openclaw/skills/spotify/`. Do NOT add a `spotify` entry under `plugins.entries` in `openclaw.json` — there is no official plugin; Spotify is skill + adapter only.
- **openclaw CLI missing in container:** by design. Use `docker exec jarvis-jarvis-1 node dist/index.js …` or `docker compose run --rm jarvis …` instead.
