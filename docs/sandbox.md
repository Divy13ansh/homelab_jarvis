# Sandbox — What / Why / How

## What

OpenClaw Docker sandbox for isolated code execution. Host stays safe from generated code.

## Why

Coding tasks must install deps, run tests, build projects without risking homelab. OpenClaw's native sandbox already provides `network:none`, `readOnlyRoot`, `capDrop:ALL`, `no-new-privileges`.

## How

### Enable

Edit `config/openclaw.json` (currently `mode: off` for bootstrap). For coding phases:

```json5
{
  agents: {
    defaults: {
      sandbox: {
        mode: "all",
        backend: "docker",
        scope: "session",
        workspaceAccess: "rw",
        docker: {
          image: "openclaw-sandbox:bookworm-slim",
          network: "none",
          readOnlyRoot: true,
          capDrop: ["ALL"]
        },
        networkAllow: ["web_fetch", "web_search"],
        networkExecAllow: ["gh"],
        networkDocker: { network: "bridge" }
      }
    }
  }
}
```

- `mode: all` — every tool exec sandboxed; `non-main` leaves main session unsandboxed if preferred.
- `scope: session` — one container per session, survives multiple tool calls.
- `workspaceAccess: rw` — sandbox mounts `/workspace` rw; `/data/projects` via binds if needed.

Compose already mounts `/var/run/docker.sock` for this.

### Workspace

```
/data/projects/<name>/{source, artifacts, metadata}
# git is source of truth; no custom DB
```

### Internet for installs

Default `network: none` (secure). When task needs `npm install`/`pip install`/`git clone`:

- OpenClaw temporarily enables `network: bridge` + `user: 0:0` for that exec scope, then terminates sandbox. Never grant host networking globally.

### Verify

```
User: Create a small Python project and run its tests.
Jarvis: exec (sandbox) → write → pip install (bridged) → pytest → report
# host unaffected; check docker ps — sandbox containers ephemeral
```

### After change

```bash
# if using openclaw cli inside container
docker compose run --rm jarvis node dist/index.js sandbox recreate --all
```
