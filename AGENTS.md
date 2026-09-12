# AGENTS.md — Jarvis Build Notes

## Commands

```bash
docker compose config        # validate compose
docker compose up -d         # start jarvis + cloudflared (+ voice when enabled)
docker compose logs -f jarvis
docker compose logs -f cloudflared
docker compose logs -f voice
curl -fsS http://127.0.0.1:18789/healthz
curl -fsS http://127.0.0.1:18789/readyz
docker compose run --rm jarvis node dist/index.js channels list
docker compose run --rm jarvis node dist/index.js pairing list discord
python -m ruff check . && python -m mypy .
```

## Conventions

- Do not hardcode secrets. All secrets in `.env` (gitignored) and referenced via `${VAR}` or SecretRef.
- Prefer OpenClaw built-in tool > plugin/channel > skill > tiny adapter.
- Pin no version as `latest-browser` per env; do not add infra without demonstrated need.
- Docs live in `docs/` — every component must have What/Why/How.

## Lint / Typecheck

```bash
ruff check .
mypy .
```
