# Voice Bridge — What / Why / How

## What

`voice/livekit_agent.py`: LiveKit `AgentSession` with Gateway LLM. `entrypoint.sh`: supervisor that starts Gateway → waits `/healthz` → starts bridge.

## Why

Single container with two processes needs ordering, health, SIGTERM. Bridge must not duplicate OpenClaw capabilities.

## How

### Bridge

```python
session = AgentSession(
  stt=inference.STT(...),
  llm=openai.LLM(base_url=GATEWAY_URL, api_key=TOKEN),  # points to OpenClaw /v1
  tts=inference.TTS(...),
  vad=silero.VAD.load(),
  turn_detection=MultilingualModel(),
  preemptive_generation=True,
)
await session.start(agent=JarvisAgent(), room=ctx.room, ...)
```

### Entrypoint

```bash
node dist/index.js gateway --port 18789 --bind loopback --token $TOKEN &
wait_for_health http://127.0.0.1:18789/healthz
python3 /app/voice/livekit_agent.py &   # if LIVEKIT_URL set
wait $gateway_pid  # propagate exit
trap TERM → kill both
```

### Session

- `AgentServer().rtc_session(agent_name="jarvis")` dispatches jobs.
- All user turns in same LiveKit room hit same OpenClaw session (gateway session key = room name).
- Long tasks: bridge streams initial ack, OpenClaw continues background.

### Deps

`voice/requirements.txt`: `livekit-agents[openai,silero,turn-detector]==1.8.1`, `python-dotenv`, `httpx`, `openai`.
