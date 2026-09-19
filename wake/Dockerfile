# jarvis-ears: wake-word gate + mic/speaker bridge into the LiveKit room.
# Tiny box: openWakeWord (fully offline) + livekit rtc client + ALSA tools.
# The OpenClaw brain (STT/TTS/skills) stays where it is; this only adds ears.
# Python 3.11: tflite-runtime (openwakeword dep) publishes no cp312 wheels.
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    libasound2 alsa-utils \
  && rm -rf /var/lib/apt/lists/* \
  && groupadd -f audio \
  && useradd -m -s /bin/bash ears \
  && mkdir -p /models /home/ears/.cache && chown -R ears:ears /models /home/ears

WORKDIR /app
COPY requirements.txt /app/requirements.txt
# Official model fetch (release assets, .tflite + .onnx + feature models).
RUN pip install --no-cache-dir -r /app/requirements.txt \
  && python -c "from openwakeword.utils import download_models; download_models(model_names=['hey_jarvis_v0.1'])" \
  && ls /usr/local/lib/python*/site-packages/openwakeword/resources/models/ \
  && chown -R ears:ears /home/ears

COPY jarvis_ears.py /app/jarvis_ears.py

USER ears
CMD ["python", "jarvis_ears.py"]
