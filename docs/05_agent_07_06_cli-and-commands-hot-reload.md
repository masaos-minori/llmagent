---
title: "Agent CLI and Commands"
category: agent
tags:
  - agent
  - agent
  - cli
  - commands
  - repl
  - slash-commands
related:
  - 05_agent_00_document-guide.md
---

# Agent CLI and Commands

load`)

`/reload` loads all 12 base config files (see [Configuration doc](05_agent_08_01_configuration-loading-agent-config.md)) and applies changes where possible. Startup-only settings are detected but not applied.

### Output format

```
Config reloaded — some changes require restart
WARNING: Some settings require restart to take effect.
Restart required: [4 items]
  [RESTART] - server1
  [RESTART] - mcp/server.url
  [RESTART] - mcp/server.startup_mode
  [RESTART] - mcp/server2.auth_token
Applied (runtime): [3 items]
  [OK] - llm
  [OK] - hist_mgr
  [OK] - tools
Startup-only (ignored): [1 items]
  [STARTUP-ONLY] - use_memory_layer
```

If nothing changed: `No changes detected.`
If all changes applied: `Config reloaded — all changes applied`
If the file cannot be read: `Reload failed (I/O error): <message>`

### Reload classification summary

| Category | `/reload` output tag | Description |
|---|---|---|
| Hot-reloadable | `[OK]` | Applied immediately to the running process |
| Restart-required | `[RESTART]` | Requires full agent restart |
| Startup-only | `[STARTUP-ONLY]` | Read once at boot; ignored by `/reload` even if changed |
| Skipped | `[SKIP]` | Changes intentionally ignored, not MCP server definitions — see Restart-required |

See [Configuration: Config file reload eligibility](05_agent_08_01_configuration-loading-agent-config.md#config-file-ownership-and-hot-reload-eligibility) for the full per-field classification matrix.

---

## Migration Notes

## Related Documents

- `agent`
- `cli`
- `commands`

## Keywords

agent
cli
commands
repl
slash-commands
