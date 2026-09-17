# spotifyd sidecar — headless Spotify Connect endpoint for server speakers.
# Pinned upstream binary (no unofficial images); ALSA direct (no Pulse running on host).
ARG SPOTIFYD_VERSION=0.4.2
FROM debian:bookworm-slim AS fetch
ARG SPOTIFYD_VERSION
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl \
  && rm -rf /var/lib/apt/lists/* \
  && curl -fSL -o /tmp/spotifyd.tgz \
    "https://github.com/Spotifyd/spotifyd/releases/download/v${SPOTIFYD_VERSION}/spotifyd-linux-x86_64-slim.tar.gz" \
  && mkdir -p /out && tar -xzf /tmp/spotifyd.tgz -C /out && chmod +x /out/spotifyd

FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    libasound2 alsa-utils \
  && rm -rf /var/lib/apt/lists/* \
  && useradd -m -s /bin/bash spotifyd \
  && mkdir -p /cache && chown spotifyd:spotifyd /cache
COPY --from=fetch /out/spotifyd /usr/local/bin/spotifyd
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh
USER spotifyd
VOLUME ["/cache"]
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
