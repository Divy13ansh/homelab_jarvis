# Channels — Discord

## What

Discord is Jarvis's primary messaging channel, via OpenClaw's official `@openclaw/discord` plugin. No custom Discord client.

## Why

OpenClaw already provides channel routing, `message` tool, pairing (`dmPolicy: pairing`), and group policies. We only configure.

## How

### 1. Create bot

1. https://discord.com/developers/applications → New Application → `Jarvis`
2. Bot → Add Bot → enable **Message Content Intent** (+ Server Members Intent if you need guild member list)
3. Bot → Reset Token → copy `DISCORD_BOT_TOKEN` → add to `.env`
4. OAuth2 → URL Generator → scopes `bot` + `applications.commands` → permissions `View Channel`, `Send Messages`, `Read Message History`, `Embed Links`, `Attach Files` → copy URL → invite to your guild
5. Optional: copy guild ID (Developer Mode → right-click server → Copy ID) → `DISCORD_GUILD_ID`

### 2. Configure OpenClaw

In `config/openclaw.json` (already present):

```json5
{ channels: { discord: {
  enabled: true,
  token: { source: "env", id: "DISCORD_BOT_TOKEN" },
  dmPolicy: "pairing",
  groupPolicy: "allowlist",
  guilds: { "<guildId>": { requireMention: true } }
}}}
```

For pairing allowlist `allowFrom: ["<discord-user-id>"]` after first pairing.

### 3. Pair

```bash
docker compose up -d jarvis
docker compose logs -f jarvis
# DM the bot on Discord → you get a pairing code
docker compose run --rm jarvis node dist/index.js pairing list discord
docker compose run --rm jarvis node dist/index.js pairing approve discord <CODE>
docker compose run --rm jarvis node dist/index.js channels list
```

Then:

```
You (Discord DM): hello jarvis
Jarvis: ... (via OpenClaw agent)
You: message Nikhil on Telegram ...  # same message tool, different target
```

### 4. Policies

- `dmPolicy: pairing` — unknown users must be approved
- `groupPolicy: allowlist` + `requireMention: true` — groups only respond when @mentioned unless allowlisted
- Streaming via `partial|block|progress` (default `partial`)

### Troubleshooting

- **Bot offline:** check `DISCORD_BOT_TOKEN` correct, intents enabled, `docker compose logs -f jarvis | grep discord`.
- **No pairing code:** ensure Gateway reachable (`127.0.0.1:18789/healthz`), token auth ok.
- **Guild message not answered:** `requireMention` — @mention the bot or add guild to `allowFrom`.

## Deferred

- Telegram (`@openclaw/telegram` via `TELEGRAM_BOT_TOKEN`) and WhatsApp (`@openclaw/whatsapp` QR login) remain plugin-install + pairing, no code. Enable when needed by adding `channels.telegram` / `channels.whatsapp` to `openclaw.json`.
