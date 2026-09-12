---
name: spotify
description: Control Spotify playback (search, play, queue, pause, next, volume) via Web API adapter
user-invocable: true
disable-model-invocation: false
metadata:
  openclaw:
    requires:
      env: ["SPOTIFY_CLIENT_ID", "SPOTIFY_CLIENT_SECRET"]
---

# Spotify

For "play Radiohead", "queue X", "pause", "next", "volume 50%":

1. **Resolve** — If track/artist ambiguous, `web_search` for disambiguation, then use `exec` to call `python3 /app/voice/spotify_adapter.py search --query "<query>"`.
2. **Control** — Call adapter:
   - `python3 /app/voice/spotify_adapter.py play --query "<query>" [--device <name>]`
   - `python3 /app/voice/spotify_adapter.py queue --uri <spotify:track:...>`
   - `python3 /app/voice/spotify_adapter.py pause|next|prev|volume --value 50`
   - `python3 /app/voice/spotify_adapter.py status`
3. **Auth** — Adapter handles OAuth token refresh from `/home/node/.openclaw/spotify.json` (refresh token). If not authenticated, instruct user to run `python3 /app/voice/spotify_adapter.py auth` and follow URL.
4. **Confirm** — Report what started playing, device, and queue state. Do not build a music service; adapter is tiny wrapper over Web API.
