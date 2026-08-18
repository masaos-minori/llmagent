## Title

Diagnostics Config Hot-Reloadability

### Context

Whether diagnostics config can be hot-reloaded at runtime via `/reload` command.

### Decision

**Hot-reloadable.** Changes take effect immediately on next operation.

### Rationale

`DiagnosticStore._load_diagnostics_config()` reads fresh config from TOML on every call. No caching layer exists between config load and usage.

### Evidence

- `scripts/agent/diagnostic_store.py:43`: `_load_diagnostics_config()` method loads from TOML each time
- Same method called in `save()`, `purge_expired_sessions()`, `get_session_diagnostics()`, `encrypt_content_if_needed()`
- No class-level cache or singleton pattern for diagnostics config

### Follow-up Actions

None required. Current design supports hot-reload.
