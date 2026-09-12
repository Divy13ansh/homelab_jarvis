# Research — What / Why / How

## What

Multi-source research using OpenClaw's `web_search`, `web_fetch`, and `browser` — orchestrated by `skills/research/SKILL.md`. No custom research engine.

## Why

OpenClaw already provides search, fetch, and isolated browser automation. A skill (Markdown workflow) is enough to teach repeatable procedure — avoids rebuilding an engine.

## How

### Skill workflow

See `skills/research/SKILL.md`: plan → 2–3 searches → fetch 4–6 sources → cross-check ≥2 → synthesize with citations → write `/data/documents/research/YYYY-MM-DD-<slug>.md` → convert if needed → deliver via `message`.

### Example

```
User (Discord): Research the current best open-source local LLMs and send me a PDF.
Jarvis: web_search (local LLM 2026, ollama vs llama.cpp, gpu requirements)
       web_fetch ×5, cross-check
       write /data/documents/research/2026-09-12-local-llms.md
       create_document --format pdf
       message (Discord) with pdf
       "Done — 5 sources, PDF at ... , sent via Discord."
```

### Verification rule

Distinguish "README claims" vs "verified by running". Flag unverified.

### Configuration

Already enabled in `config/openclaw.json`:

```json5
{ tools: { web: { search: { enabled: true }, fetch: { enabled: true } }, browser: { enabled: true } } }
```

Requires browser image (`latest-browser`) — baked Chromium, no runtime install.

### Restrictions

- Do not create `skills/search-web/SKILL.md` (wraps one tool). Research is multi-step → skill justified.
- Do not implement custom vector DB until OpenClaw memory/sessions insufficient.
