# Voice — Cloud deploy — What / Why / How

## What

Run the Jarvis voice agent on LiveKit Cloud (project `p_5k6ua1ii1c8`) so STT/VAD/TTS compute leaves the homelab. The homelab OpenClaw Gateway remains the LLM at `https://jarvis.divy13ansh.in/v1`, so all skills/tools (research, spotify, message, exec, browser) keep working with zero re-implementation.

## Why

Homelab is behind CGNAT with limited headroom. Cloud handles realtime media + inference (STT/TTS); homelab only answers LLM calls through the tunnel. Yes, deploying from your Mac makes sense: the `lk` CLI can't install on the homelab host (no PyPI package, SSL handshake fails on the install script), and `brew install livekit-cli` works on macOS. Deployment uploads to Cloud, so homelab is unaffected.

## How (on the Mac)

```bash
brew install livekit-cli
lk cloud auth                      # log in, select project p_5k6ua1ii1c8
cd jarvis/voice                    # deploy from existing agent code, NOT the starter template
lk agent create --name jarvis      # confirm flags with `lk agent create --help`
```

Build source is `voice/Dockerfile` (python:3.12-slim + `requirements.txt` + `livekit_agent.py`, CMD `start`).

### Secrets (LiveKit dashboard → agent → Secrets, never in git)

| Variable | Value |
|---|---|
| `OPENCLAW_GATEWAY_URL` | `https://jarvis.divy13ansh.in/v1` |
| `OPENCLAW_GATEWAY_TOKEN` | same as homelab `.env` |
| `OPENCLAW_VOICE_MODEL` | `openclaw` (gateway agent route — verified. Gateway `/v1` rejects provider ids like `azure/gpt-5.4-mini` with 400; the route resolves to the default agent model server-side) |
| `LIVEKIT_URL` / `LIVEKIT_API_KEY` / `LIVEKIT_API_SECRET` | from Cloud project settings |

Then deploy (`lk deploy` or dashboard Deploy — confirm exact subcommand with `lk --help` on the Mac).

### Dispatch + test

- Agent name: `jarvis` (matches `@server.rtc_session(agent_name="jarvis")`).
- Join/create room `jarvis` via Cloud dashboard “Try room” or JS SDK `createRoom({url, roomName: 'jarvis'})`.
- Expect greeting (“Greet the user warmly as Jarvis, briefly.”), then natural turn-taking with interruptions.
- Dashboard sessions 0 → 1 confirms the path. Long tasks (“research X, send PDF”) reply “On it.” then deliver via Discord.

### Fallback (no Cloud deploy)

The `jarvis` container already runs the same bridge as a self-hosted worker when `LIVEKIT_URL/KEY` are set (`entrypoint.sh` → `python3 /app/voice/livekit_agent.py start`). Same room-join test applies; Cloud still relays media.

### Troubleshooting

- **Agent never joins:** secrets missing/mismatched, or gateway `/v1` unreachable from Cloud — test `curl -H "Authorization: Bearer $TOKEN" https://jarvis.divy13ansh.in/readyz` from outside the LAN.
- **LLM 400/errors:** model must be `azure/gpt-5.4-mini`; gateway provider `api` is `openai-completions` with base `.../openai/v1`.
- **`turn_detector` deprecation:** warning only; pinned `livekit-agents==1.8.1` still ships `MultilingualModel`.
