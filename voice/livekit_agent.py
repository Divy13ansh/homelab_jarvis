#!/usr/bin/env python3
import logging
import os

from dotenv import load_dotenv

load_dotenv()

from livekit.agents import Agent, AgentServer, AgentSession, inference, room_io
from livekit.plugins import openai, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("jarvis-voice")

GATEWAY_URL = os.environ.get("OPENCLAW_GATEWAY_URL", "http://127.0.0.1:18789/v1")
GATEWAY_TOKEN = os.environ.get("OPENCLAW_GATEWAY_TOKEN", "")
LIVEKIT_URL = os.environ.get("LIVEKIT_URL", "")
MODEL = os.environ.get("OPENCLAW_VOICE_MODEL", "openclaw/default")

class JarvisAgent(Agent):
    def __init__(self):
        super().__init__(instructions=(
            "You are Jarvis, a helpful personal AI assistant. "
            "Be concise, natural, and proactive. "
            "For long tasks say 'On it' then continue in background via chat."
        ))

server = AgentServer(multiprocessing_context="spawn")

@server.rtc_session(agent_name="jarvis")
async def entrypoint(ctx):
    gateway_llm = openai.LLM(
        model=MODEL,
        base_url=GATEWAY_URL,
        api_key=GATEWAY_TOKEN or "not-needed",
    )

    vad = silero.VAD.load()

    session = AgentSession(
        stt=inference.STT(model="deepgram/nova-3", language="multi"),
        llm=gateway_llm,
        tts=inference.TTS(model="cartesia/sonic-3", voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"),
        vad=vad,
        turn_detection=MultilingualModel(),
        preemptive_generation=True,
    )

    room_id = getattr(ctx.room, "name", "unknown")
    logger.info("voice session start room=%s gateway=%s model=%s", room_id, GATEWAY_URL, MODEL)

    await session.start(
        agent=JarvisAgent(),
        room=ctx.room,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(noise_cancellation=None),
        ),
    )
    await session.generate_reply(instructions="Greet the user warmly as Jarvis, briefly.")

if __name__ == "__main__":
    if not LIVEKIT_URL:
        logger.warning("LIVEKIT_URL not set — agent will not connect until configured")
    from livekit.agents import cli
    cli.run_app(server)
