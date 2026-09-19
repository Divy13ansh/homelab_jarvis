#!/bin/bash
set -euo pipefail

# Unmute + sane level on card 0 (ALSA boots muted on many boards).
amixer -c 0 set Master unmute >/dev/null 2>&1 || true
amixer -c 0 set PCM unmute >/dev/null 2>&1 || true
amixer -c 0 set Master 90% unmute >/dev/null 2>&1 || true
# Auto-Mute silences speakers on phantom jack-detect; this box has no
# headphones attached, so keep it off.
amixer -c 0 set 'Auto-Mute Mode' Disabled >/dev/null 2>&1 || true

CONF="/tmp/spotifyd.conf"
{
  echo "[global]"
  echo "backend = \"alsa\""
  echo "device = \"${SPOTIFYD_ALSA_DEVICE:-default}\""
  echo "mixer = \"${SPOTIFYD_MIXER:-Master}\""
  echo "control = \"${SPOTIFYD_MIXER:-Master}\""
  echo "device_name = \"${SPOTIFYD_DEVICE_NAME:-jarvis-server}\""
  echo "device_type = \"speaker\""
  echo "bitrate = 320"
  echo "initial_volume = ${SPOTIFYD_INITIAL_VOLUME:-100}"
  echo "volume_normalisation = true"
  echo "normalisation_pregain = ${SPOTIFYD_PREGAIN:-0}"
  echo "cache_path = \"/cache\""
  echo "max_cache_size = 1073741824"
  echo "zeroconf_port = 4467"
  echo "autoplay = false"
  # Username/password left empty -> Spotify-app discovery login (zeroconf).
  # Set SPOTIFYD_USERNAME/SPOTIFYD_PASSWORD to use credential auth instead.
  if [ -n "${SPOTIFYD_USERNAME:-}" ]; then
    echo "username = \"${SPOTIFYD_USERNAME}\""
  fi
  if [ -n "${SPOTIFYD_PASSWORD:-}" ]; then
    echo "password_cmd = \"echo \\\"\\$SPOTIFYD_PASSWORD\\\"\""
  fi
} > "${CONF}"
chmod 600 "${CONF}"

echo "[spotifyd] device='${SPOTIFYD_DEVICE_NAME:-jarvis-server}' alsa='${SPOTIFYD_ALSA_DEVICE:-default}'"
exec /usr/local/bin/spotifyd --config-path "${CONF}" --no-daemon
