# Voice — Wake Word — What / Why / How

## What

`wake/` container (`jarvis-ears`): always-on "hey jarvis" detection on the server mic + mic/speaker bridge into the existing LiveKit room. The OpenClaw brain, STT/TTS, and all skills are untouched and reused.

## Why

Playground tabs and Discord require a screen. A voice assistant should work hands-free across the room. The wake gate also keeps the mic muted 99% of the time (privacy + no idle STT cost) while the room stays alive (context persists across wakes).

## How

### Components (all in `wake/jarvis_ears.py`, ~250 lines)

- **Wake**: openWakeWord 0.6.0, official `hey_jarvis` ONNX model (baked at build via `download_models`), fully offline, no accounts/keys. Python 3.11 base (tflite-runtime has no cp312 wheels). Sensitivity via `WAKE_SENSITIVITY` (default 0.5).
- **Mic**: `arecord hw:0,0` stereo 44.1k → downmix + `audioop.ratecv` to 16k mono (wake) and 48k mono (LiveKit `AudioSource`). No PortAudio dependency.
- **Room**: joins `LIVEKIT_ROOM` as `jarvis-ears` at startup (token minted via `livekit-api`), publishes a gated mic track, subscribes to agent audio → `aplay hw:0,0`.
- **States**: IDLE (wake loop) → wake → earcon + pause Spotify (only if playing) + unmute → ACTIVE (half-duplex: mic frames dropped while agent audio hot) → `WAKE_IDLE_TIMEOUT` (12s) of silence → mute + resume music + IDLE.
- **Spotify pause/resume**: reuses `/app/voice/spotify_adapter.py` (mounted ro) with token from the shared `openclaw-data` volume (rw — hourly refresh must write).

### Run (opt-in profile — mic always-on is a deliberate choice)

```bash
docker compose --profile wake up -d wake
docker compose logs -f wake   # expect: model loaded → joined → listening
```

Tune: `WAKE_SENSITIVITY` (fewer misses vs false alarms), `MIC_ACTIVITY_RMS`, `WAKE_IDLE_TIMEOUT`. Test: say "hey jarvis" → earcon → speak → reply on server speakers.

### Troubleshooting

| Symptom | Check |
|---|---|
| Never wakes | mic capture: `arecord -D hw:0,0` in any audio container; lower `WAKE_SENSITIVITY` (0.4); room noise floor vs `MIC_ACTIVITY_RMS` |
| Wakes constantly | raise sensitivity (0.6–0.7); TV/radio near laptop |
| Agent talks to itself | half-duplex gate (`agent_audio_until`) — check logs; increase 0.8s window |
| TTS fails while music plays | wake pauses Spotify first; if `hw:0,0` busy, `aplay` fails — pause path covers it |
| Room join fails | `LIVEKIT_URL/KEY/SECRET` in `.env`; worker registered (`logs jarvis \| grep registered`) |
