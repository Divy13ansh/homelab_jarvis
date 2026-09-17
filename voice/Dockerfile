# LiveKit Cloud agent image — builds the Jarvis voice bridge for `lk deploy`.
# Homelab Gateway stays the LLM; this image only handles STT/VAD/TTS/turns.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN apt-get update && apt-get install -y --no-install-recommends gcc \
  && rm -rf /var/lib/apt/lists/* \
  && pip install --no-cache-dir -r /app/requirements.txt \
  && python -m livekit.agents download-files || true

COPY livekit_agent.py spotify_adapter.py /app/

CMD ["python", "livekit_agent.py", "start"]
