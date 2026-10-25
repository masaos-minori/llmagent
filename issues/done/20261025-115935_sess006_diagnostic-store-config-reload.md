# Resolve diagnostics config once per DiagnosticStore operation

## Priority
Medium

## Summary
`DiagnosticStore` re-reads and re-parses `agent.toml` up to three times inside a
single `save()` call (and once per `fetch()`), because every internal helper
independently calls `_load_diagnostics_config()` and `ConfigLoader.load` has no
cache. Resolve the diagnostics config once per public operation and reuse it.

## Background
`scripts/agent/diagnostic_store.py` documents the pattern deliberately (docstring
lines 43-51: "mirrors the RetentionConfig.from_config() pattern" because
DiagnosticStore has no AgentContext reference). That pattern was designed for
once-per-command maintenance operations; `DiagnosticStore` instead sits on the
event/turn path (`AgentSession.save_diagnostic`, transport-failure and partial-
completion events, `session_persister` summaries), so the same pattern becomes a
repeated hot-path file read.

## Problem
Confirmed by code reading (Evidence: confirmed, Confidence: High):

- `save()` (lines 135-183) triggers `_purge_old_diagnostics()` -> config load at
  line 115, `_filter_sensitive_fields()` -> config load at line 90 (JSON-object
  payloads), and the encryption check -> config load at line 164: up to 3 full
  `ConfigLoader().load("agent.toml")` calls per saved diagnostic.
- `fetch()` loads the config again (line 187).
- `ConfigLoader().load` re-parses the TOML file on every call (no caching in
  `scripts/shared/config_loader.py`).

Side effect beyond cost: the three loads within one `save()` can observe different
config states if `agent.toml` changes mid-call, so the redaction and encryption
decisions of one diagnostic can come from inconsistent snapshots.

## Reason for Change
Redundant full-file config parses on a repeated path, plus a small consistency
window in a security-relevant decision (sensitive-field redaction gating
encryption). The fix is contained to one class.

## Implementation Intent
Load the diagnostics config once per public operation (`save`, `fetch`, the
serialization-event helpers) and pass the resolved `DiagnosticsConfig` into the
private helpers instead of having each helper re-load it. Keep config acquisition
inside the existing config boundary (`ConfigLoader` / `agent.toml`, per
`skills/DESIGN.md` config boundaries); do not build a second config system.

## Target Files or Areas
- scripts/agent/diagnostic_store.py
- tests/agent/ (diagnostic store tests)

## Required Changes
- Load `DiagnosticsConfig` once per public method and thread it through
  `_filter_sensitive_fields`, `_purge_old_diagnostics`, and the encryption check.
- Keep behavior identical for every existing call site.
- Add a test asserting a single config load per `save()`.

## Constraints
- Hot-reload semantics today are "next save sees the new config"; if caching
  across calls is chosen instead, the staleness contract must be explicit
  (see Unresolved Questions) — per-call single load is the safe default.
- Do not change `DiagnosticStore`'s public method signatures unless planning
  decides to inject config via AgentContext (constructor surface change needs its
  own decision).
- The sensitive-field redaction and the no-encryption RuntimeError path must keep
  exactly their current trigger conditions.

## Acceptance Criteria
- A spy on `ConfigLoader.load` shows at most one `agent.toml` load per `save()`
  (for JSON-object payloads) and per `fetch()`.
- All existing diagnostic-store tests pass unchanged.
- Redaction/encryption behavior is byte-identical for the same inputs.

## Testing Expectations
- New unit test: count config loads per `save()` / per `fetch()`.
- Run the existing diagnostic-store and session-persister test modules.
- `uv run ruff check` and `uv run mypy --no-namespace-packages` on the changed file.

## Documentation Impact
Documentation update required only for the resolved semantics:
`docs/23_agent/agent_10_05_operations-and-observability-monitoring.md` should state
when diagnostics config changes take effect (per-save snapshot, or the documented
cache freshness if caching is chosen). If caching is chosen and its invalidation
is unverified, record a Needs Confirmation item.

## Out of Scope
- Adding a global config cache to `ConfigLoader` (repository-wide change, needs
  its own issue/plan).
- Changing `DiagnosticStore`'s storage schema or encryption scheme.

## Dependencies
- N/A: none

## Unresolved Questions
- Per-call single load vs a store-level cached config with a documented refresh
  rule. 不明 — decide in planning based on whether hot-reload of diagnostics
  config mid-session is an operational requirement.
- Whether `DiagnosticStore(self.session_id)` binding at construction
  (`scripts/agent/session.py` line 52) should be revisited while touching this
  class; today every `save()` passes explicit ids, so it is behavior-neutral.
  不明 — not in scope unless planning finds a need.

## AI Implementation Instruction
Refactor within `diagnostic_store.py` only: pass the resolved config object into
private helpers; do not duplicate loads at call sites. Add the load-count test
first. Preserve the existing exception contract (`RuntimeError` on sensitive
content without encryption).

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261025-115935
- **Related target files**: scripts/agent/diagnostic_store.py, tests/agent/ (diagnostic store tests)
