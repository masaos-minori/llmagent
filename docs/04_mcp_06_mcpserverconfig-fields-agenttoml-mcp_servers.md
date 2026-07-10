---
title: "McpServerConfig Fields (agent.toml `[mcp_servers.*]`)"
category: mcp
tags:
  - mcp
  - configuration
related:
  - 04_mcp_00_document-guide.md
  - 04_mcp_06_configuration_and_operations.md
source:
  - 04_mcp_06_configuration_and_operations.md
---

# McpServerConfig Fields (agent.toml `[mcp_servers.*]`)

## McpServerConfig Fields (agent.toml `[mcp_servers.*]`)

| Field | Type | Default | Description |
|---|---|---|---|
| `transport` | `TransportType` | required | `TransportType.HTTP` (`"http"`); TOML string values are converted by the config loader, not at runtime |
| `url` | `str` | required | HTTP server base URL |
| `startup_mode` | `str` | `"none"` | `"none"` / `"persistent"` / `"subprocess"` |
| `cmd` | `list[str]` | `[]` | Launch command for `startup_mode=subprocess`; must be non-empty when subprocess mode is used |
| `env` | `dict[str, str]` | `{}` | Extra environment variables passed to the subprocess |
| `healthcheck_mode` | `str` | *(derived)* | `"http"` — the only current transport/healthcheck mode; derived automatically when the key is omitted. If present, the value must be exactly `"http"`. |
| `idle_timeout_sec` | `int` | `0` | subprocess auto-stop delay (0 = disabled) |
| `startup_timeout_sec` | `int` | `30` | subprocess mode: health poll timeout |
| `call_timeout_sec` | `float` | `60.0` | per-call timeout for HttpTransport; 0 = no timeout |
| `tool_names` | `list[str]` | `[]` | Validation hint (optional); registry routes regardless. Empty = no validation. See [Routing Source of Truth](04_mcp_03_routing_lifecycle_and_execution.md#routing-source-of-truth). |
| `auth_token` | `str` | `""` | Bearer token for auth (empty = no auth) |

> `auth_token=""` (no Bearer auth) is allowed only in
> `security_profile="local"`; it is rejected at startup in
> `security_profile="production"`. See
> [04_mcp_05 §Authentication](04_mcp_05_security_and_safety_model.md#authentication-auth_token)
> and [§Security Profile](04_mcp_05_security_and_safety_model.md#security-profile-security_profile)
> for the full local/production distinction and enforcement point.

**Deprecation note:** Earlier versions accepted `healthcheck_mode=""` as an explicit request for auto-inference (compatibility with configs predating this field). That empty-string sentinel has been removed — omit the key entirely to get the derived value, or set it to the exact string `"http"`. An explicit empty string is now rejected as an invalid value, the same as any other unrecognized string.

| `role` | `str` | `""` | Human-readable role label for `/mcp` display |

**`startup_mode="none"`:** the server is neither spawned as a subprocess nor health-checked
at startup. Every tool call routed to it is rejected immediately by
`ToolExecutor._check_startup_mode()` with a `"disabled (startup_mode=none)"` error, before
any network attempt. This is the default when `startup_mode` is omitted from config —
a server must opt in to `"persistent"` or `"subprocess"` to be usable.

**Validation rules:**
- `transport="http"` → `url` must be non-empty and a valid HTTP/HTTPS URL
- `startup_mode="subprocess"` → `cmd` must be non-empty
- `call_timeout_sec` must be `>= 0` (0 = no timeout)
- `startup_timeout_sec` must be `>= 0` (0 = skip health polling)
- `tool_names` items must be non-empty strings with no duplicates
- `auth_token` must be a string
- `env` keys and values must all be strings

---


## Related Documents

- [04_mcp_06_configuration_and_operations.md](04_mcp_06_configuration-file-inventory.md)

## Keywords

configuration
