ARG OPENCLAW_IMAGE=ghcr.io/openclaw/openclaw:latest-browser
FROM ${OPENCLAW_IMAGE}

USER root

RUN apt-get update && apt-get install -y --no-install-recommends \
    tini curl jq git python3 python3-pip pandoc wkhtmltopdf \
  && rm -rf /var/lib/apt/lists/* \
  && pip3 install --no-cache-dir --break-system-packages \
    python-docx==1.1.2 weasyprint==62.3 reportlab==4.4.1

COPY scripts/healthcheck.sh /usr/local/bin/healthcheck.sh
COPY config/openclaw.json /home/node/.openclaw/openclaw.json
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/healthcheck.sh /usr/local/bin/entrypoint.sh \
  && chown -R node:node /home/node/.openclaw

USER node

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD /usr/local/bin/healthcheck.sh

ENTRYPOINT ["/usr/bin/tini", "--", "/usr/local/bin/entrypoint.sh"]
