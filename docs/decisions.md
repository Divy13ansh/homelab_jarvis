# Decisions (ADRs)

## 1. LLM: Azure OpenAI

- **Why:** User choice; enterprise homelab often has Azure credits.
- **How:** `azure` provider in `openclaw.json` with `baseUrl=${AZURE_OPENAI_ENDPOINT}`, `apiVersion`, `apiKey` SecretRef.
- **Alternative:** OpenAI/Anthropic/local Ollama — swap provider block.

## 2. LiveKit Cloud over self-hosted

- **Why:** Homelab is CGNAT + client isolation → cannot expose UDP/TURN. Cloud 10k min free solves it with zero infra, outbound 443 only.
- **How:** Bridge `openai.LLM(base_url=gateway/v1)` forwards to Gateway; Cloud handles SFU+TURN.
- **Fallback:** `--profile selfhosted` with `livekit.yaml` + `coturn` on VPS/public IP.

## 3. Discord primary, Telegram deferred

- **Why:** User uses Discord most; Telegram/WhatsApp remain plugins when needed.
- **How:** `channels.discord` enabled, others commented in `.env.example`.

## 4. Spotify adapter, not service

- **Why:** Need only playback control; Web API suffices.
- **How:** `skills/spotify` + `spotify_adapter.py`; no backend.

## 5. Cloudflared tunnel, not Tailscale

- **Why:** User has `divy13ansh.in` + `homelab` tunnel; outbound-only, no port-forward.
- **How:** `cloudflared` sidecar `network_mode: service:jarvis`, Access allowlist + Gateway token.
- **Note:** Tunnel carries only Gateway; LiveKit Cloud is direct.

## 6. Image: latest-browser, no pin

- **Why:** User explicitly chose `latest-browser` for Control UI browser.
- **Risk:** `latest` moves; pin after first green run if desired.

## 7. Sandbox enabled, no extra DB/infra

- **Why:** Strict hierarchy: built-in > plugin > skill > adapter. No vector DB/Redis/K8s without demonstrated need.
