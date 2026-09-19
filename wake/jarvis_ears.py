#!/usr/bin/env python3
"""jarvis-ears: wake-word gate + mic/speaker bridge into the LiveKit room.

IDLE: mic -> openWakeWord ("hey jarvis"), nothing leaves the box.
ACTIVE: mic published to room, agent audio played on server speakers.
The LiveKit AgentSession (OpenClaw brain, all skills) does the rest.
"""
import asyncio
import audioop
import logging
import math
import os
import struct
import subprocess
import sys
import time
import wave

from dotenv import load_dotenv

load_dotenv()

import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("jarvis-ears")

LIVEKIT_URL = os.environ["LIVEKIT_URL"]
LIVEKIT_API_KEY = os.environ["LIVEKIT_API_KEY"]
LIVEKIT_API_SECRET = os.environ["LIVEKIT_API_SECRET"]
ROOM = os.environ.get("LIVEKIT_ROOM", "jarvis")
IDENTITY = os.environ.get("LIVEKIT_EARS_IDENTITY", "jarvis-ears")
SENSITIVITY = float(os.environ.get("WAKE_SENSITIVITY", "0.5"))
IDLE_TIMEOUT = float(os.environ.get("WAKE_IDLE_TIMEOUT", "12"))
MIC_ACTIVITY_RMS = int(os.environ.get("MIC_ACTIVITY_RMS", "400"))
MIC_DEVICE = os.environ.get("WAKE_MIC_DEVICE", "hw:0,0")
SPK_DEVICE = os.environ.get("WAKE_SPK_DEVICE", "hw:0,0")

IN_RATE, IN_CH = 44100, 2      # what arecord gives us
OWW_RATE = 16000               # what openwakeword wants
LIVEKIT_RATE = 48000           # what rtc.AudioSource gets
OWW_CHUNK = 1280               # 80ms @ 16kHz, mono int16


def sh(*cmd):
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=30)
        return r.returncode == 0, (r.stdout or b"").decode(errors="replace")
    except Exception as e:
        return False, str(e)


def spotify(cmd):
    ok, out = sh("python3", "/app/voice/spotify_adapter.py", *cmd)
    return ok, out.strip()


def spotify_playing():
    import json

    ok, out = spotify(["status"])
    if not ok:
        return False
    try:
        return bool(json.loads(out or "{}").get("is_playing"))
    except Exception:
        return False


def make_earcon(path="/tmp/earcon.wav"):
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(44100)
        frames = b""
        for freq, ms in ((880, 120), (1320, 160)):
            n = int(44100 * ms / 1000)
            frames += struct.pack(
                "<" + "h" * n,
                *(int(20000 * math.sin(2 * math.pi * freq * i / 44100)) for i in range(n)),
            )
        w.writeframes(frames)
    return path


def downmix_16k(stereo441):
    mono = audioop.tomono(stereo441, 2, 0.5, 0.5)
    conv, _ = audioop.ratecv(mono, 2, 1, 44100, 16000, None)
    return conv


class Ears:
    def __init__(self):
        from livekit import rtc

        self.rtc = rtc
        self.room = rtc.Room()
        self.mic_source = None
        self.mic_track = None
        self.aplay = None
        self.active = False
        self.last_activity = 0.0
        self.paused_music = False
        # Half-duplex: mic frames are dropped while agent audio is hot so the
        # laptop mic never feeds the speakers back into STT.
        self.agent_audio_until = 0.0
        self._rs_oww = None
        self._rs_livekit = None

    async def connect(self):
        from livekit.api import AccessToken, VideoGrants

        token = (
            AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
            .with_identity(IDENTITY)
            .with_grants(VideoGrants(room_join=True, room=ROOM))
            .to_jwt()
        )
        await self.room.connect(LIVEKIT_URL, token)
        logger.info("joined room=%s as %s", ROOM, IDENTITY)
        self.mic_source = self.rtc.AudioSource(LIVEKIT_RATE, 1)
        self.mic_track = self.rtc.LocalAudioTrack.create_audio_track("mic", self.mic_source)
        await self.room.local_participant.publish_track(self.mic_track)
        logger.info("mic track published (gated)")

        @self.room.on("track_subscribed")
        def _on_track(track, _pub, _participant):
            if track.kind == self.rtc.TrackKind.KIND_AUDIO:
                asyncio.ensure_future(self._play_agent_audio(track))

    async def _play_agent_audio(self, track):
        stream = self.rtc.AudioStream(track)
        self.aplay = subprocess.Popen(
            ["aplay", "-D", SPK_DEVICE, "-f", "S16_LE", "-r", "48000", "-c", "1", "-t", "raw"],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        async for event in stream:
            frame = event.frame
            data = bytes(frame.data)
            if audioop.rms(data, 2) > 200:
                self.last_activity = time.time()
                self.agent_audio_until = time.time() + 0.8
            try:
                self.aplay.stdin.write(data)
            except BrokenPipeError:
                break

    def mic_chunks(self):
        """Yield (pcm16_mono_bytes, rms) at 16kHz from arecord stdout."""
        proc = subprocess.Popen(
            ["arecord", "-D", MIC_DEVICE, "-f", "S16_LE", "-r", str(IN_RATE),
             "-c", str(IN_CH), "-t", "raw", "-q"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            bufsize=IN_RATE * IN_CH * 2,
        )
        raw_frame = IN_RATE // 10 * IN_CH * 2  # 100ms stereo
        buf = b""
        try:
            while True:
                data = proc.stdout.read(raw_frame)
                if not data:
                    break
                mono44 = audioop.tomono(data, 2, 0.5, 0.5)
                conv, self._rs_oww = audioop.ratecv(mono44, 2, 1, IN_RATE, OWW_RATE, self._rs_oww)
                buf += conv
                while len(buf) >= OWW_CHUNK * 2:
                    chunk, buf = buf[: OWW_CHUNK * 2], buf[OWW_CHUNK * 2 :]
                    yield chunk, audioop.rms(chunk, 2)
        finally:
            proc.terminate()

    def publish_mic(self, chunk16k):
        mono48, self._rs_livekit = audioop.ratecv(chunk16k, 2, 1, OWW_RATE, LIVEKIT_RATE, self._rs_livekit)
        n = len(mono48) // 2
        step = LIVEKIT_RATE // 100  # 10ms frames
        for i in range(0, n, step):
            part = mono48[i * 2 : (i + step) * 2]
            if len(part) < step * 2:
                part = part.ljust(step * 2, b"\x00")
            frame = self.rtc.AudioFrame(
                samples_per_channel=step, sample_rate=LIVEKIT_RATE,
                num_channels=1, data=list(part),
            )
            asyncio.get_event_loop().call_soon_threadsafe(
                self.mic_source.capture_frame, frame
            )

    async def idle_loop(self, oww):
        logger.info("listening for wake word (hey jarvis)")
        for chunk, _rms in await asyncio.to_thread(self._drain_mic, oww):
            pass

    def _drain_mic(self, oww):
        # Runs in a thread; yields nothing, drives the state machine inline.
        import numpy as _np  # noqa: F401  (ensures numpy present for oww)

        for chunk, rms in self.mic_chunks():
            if not self.active:
                scores = oww.predict(_np.frombuffer(chunk, dtype=_np.int16))
                # NOTE: 0.6.0 keys scores by model filename (hey_jarvis_v0.1),
                # not the bare name — exact-key lookup silently never fires.
                score = max(
                    (s for k, s in scores.items() if "jarvis" in k.lower()),
                    default=0.0,
                )
                if score >= SENSITIVITY:
                    logger.info("wake! score=%.2f", score)
                    asyncio.run_coroutine_threadsafe(self.wake(), asyncio.get_event_loop())
                elif score >= 0.15:
                    logger.info("near-miss score=%.2f (hears speech, below %.2f)",
                                score, SENSITIVITY)
            else:
                if rms > MIC_ACTIVITY_RMS:
                    self.last_activity = time.time()
                if time.time() > self.agent_audio_until:
                    self.publish_mic(chunk)
                if time.time() - self.last_activity > IDLE_TIMEOUT:
                    asyncio.run_coroutine_threadsafe(self.sleep(), asyncio.get_event_loop())
        return []

    async def wake(self):
        if self.active:
            return
        self.active = True
        if spotify_playing():
            spotify(["pause"])
            self.paused_music = True
        sh("aplay", "-D", SPK_DEVICE, EARCON)
        self.last_activity = time.time()
        logger.info("active — speak now")

    async def sleep(self):
        if not self.active:
            return
        self.active = False
        if self.paused_music:
            spotify(["play"])  # resume, no args = resume current context
            self.paused_music = False
        logger.info("idle — listening for wake word")


EARCON = make_earcon()


def load_wake_model():
    import glob

    import openwakeword
    from openwakeword.model import Model

    base = os.path.join(os.path.dirname(openwakeword.__file__), "resources", "models")
    # 0.6.0 ships ONNX (prefer it); .tflite names are tried as fallback.
    cands = sorted(glob.glob(os.path.join(base, "hey_jarvis*.onnx")))
    cands += sorted(glob.glob(os.path.join(base, "hey_jarvis*.tflite")))
    if not cands:
        raise FileNotFoundError(f"no hey_jarvis model in {base}")
    logger.info("wake model: %s", cands[0])
    fw = "onnx" if cands[0].endswith(".onnx") else "tflite"
    return Model(wakeword_models=[cands[0]], inference_framework=fw)


async def main():
    oww = await asyncio.to_thread(load_wake_model)
    logger.info("wake model loaded")
    while True:
        try:
            ears = Ears()
            await ears.connect()
            await ears.idle_loop(oww)
        except Exception:
            logger.exception("ears crashed, reconnecting in 5s")
            await asyncio.sleep(5)


if __name__ == "__main__":
    for v in ("LIVEKIT_URL", "LIVEKIT_API_KEY", "LIVEKIT_API_SECRET"):
        if not os.environ.get(v):
            print(f"{v} not set", file=sys.stderr)
            sys.exit(2)
    asyncio.run(main())
