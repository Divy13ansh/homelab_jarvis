# Music — Server Speakers — What / Why / How

## What

`spotifyd` sidecar: the homelab box itself is a Spotify Connect speaker (`jarvis-server`), controllable by Jarvis like any other device. Pinned upstream v0.4.2 binary, ALSA direct.

## Why

Phone/laptop speakers aren't always where the user is. A headless Connect endpoint on the server (which has Intel onboard audio + speakers) makes "play on the server" work from Discord/voice with zero new Jarvis code — it's just another `--device`.

## How

### Service (`spotifyd/` + compose `spotifyd` svc)

- `spotifyd/Dockerfile`: debian-slim + `libasound2`, `alsa-utils`, **`ca-certificates`** (load-bearing — without system TLS roots the OAuth token exchange fails with `Request failed` while the browser still shows success), pinned `spotifyd-linux-x86_64-slim` binary.
- `network_mode: host` (zeroconf/mDNS needs it), `/dev/snd` passthrough, `group_add: 29` (audio), `spotifyd-cache` volume for credentials.
- Entrypoint unmutes ALSA (`Master`/`PCM`, boots muted on many boards) and renders `spotifyd.conf` from `SPOTIFYD_*` env. No username/password by default → discovery login.

### First login (client isolation blocks discovery)

mDNS advertisement can't cross the isolated WiFi, so use headless OAuth instead:

```bash
# on homelab host:
docker exec jarvis-spotifyd-1 spotifyd authenticate --oauth-port 8000 --cache-path /cache
# on Mac: ssh -L 8000:127.0.0.1:8000 <homelab>  (verify: curl -s http://127.0.0.1:8000/x)
# open the printed authorize URL in a FRESH tab, approve once, never reload
```

Verify `/cache/oauth/credentials.json` exists BEFORE restarting the daemon (the browser success page renders even when the exchange fails; a restart mid-save wipes it). Each attempt mints a new PKCE verifier — stale tabs/callback URLs always fail; always use the newest URL. Then `docker compose restart spotifyd` and confirm `jarvis-server` in `devices`.

### Use

```bash
docker exec jarvis-jarvis-1 python3 /app/voice/spotify_adapter.py devices
docker exec jarvis-jarvis-1 python3 /app/voice/spotify_adapter.py play --query "Cheema Y" --device "jarvis-server"
```

Discord/voice: "play X on the server" → Jarvis targets `jarvis-server`.

### Driver quirk (Timi/Mi Notebook, speakers work on Windows, silent on Ubuntu)

The SOF driver (`sof-audio-pci-intel-cnl`) streams perfectly (PCM RUNNING, mixers up) but the ALC256 speaker path stays silent — known quirk on this board. Fix: force the legacy HDA driver via `/etc/modprobe.d/timi-audio-fix.conf`:

```
options snd-intel-dspcfg dsp_driver=1
```

Then `sudo update-initramfs -u` and **reboot** (module option applies at load; runtime rebind was attempted and refused). Containers (`restart: unless-stopped`) come back automatically. Verify after reboot: `cat /proc/asound/cards` should show HDA-Intel instead of `sof-hda-dsp`, then `speaker-test` for a tone.

### Troubleshooting

| Symptom | Check |
|---|---|
| `devices` lacks jarvis-server | daemon running? `logs spotifyd` shows Authenticated? credentials in `/cache`? |
| OAuth `Request failed` | `ca-certificates` in image; fresh tab; newest URL only |
| 204 ok but `is_playing:false` | app/device asleep — same as any client; for server check `logs spotifyd` for `loaded` lines and ALSA mixer levels |
| No sound, track loads | `amixer` levels in container; correct ALSA device (`SPOTIFYD_ALSA_DEVICE`, default uses dmix); speakers physically connected |
