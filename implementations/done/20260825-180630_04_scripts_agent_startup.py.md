## Goal

`REQ-002`/`REQ-003` (partial): extend the startup readiness log's "Excluded tools
(unavailable)" line to show which `failure_policy` was applied for each excluded
server, implementing ADR-004 Decision #5's observability requirement.

## Scope

- **In-Scope**: extend the log line at `scripts/agent/startup.py:565-568` to include
  each excluded server's `failure_policy` value; add a test asserting this to
  `tests/agent/test_startup.py`.
- **Out-of-Scope**: the `discover_all()` decision logic itself — covered by the
  companion `scripts/agent/services/mcp_tool_discovery.py` implementation procedure
  document (REQ-001); `degraded_keys`/`Degraded servers` log line (lines 550-556) —
  unrelated to `failure_policy`, not touched by this Requirement.

## Assumptions

- Confirmed via Read (`scripts/agent/startup.py:557-568`) that the current log line
  reads `f"  Excluded tools (unavailable): {', '.join(sorted(unavailable_servers))}"`,
  built from `runtime_tools.unavailable_servers` (a `frozenset[str]` of server keys with
  no `failure_policy` information attached).
- **Critical finding**: `unavailable_servers` (`RuntimeToolRegistry`'s field, populated
  by `discover_all()`) is a plain `frozenset[str]` of server keys — it carries no
  per-server `failure_policy` value. To render `failure_policy` per server in this log
  line, `startup.py` must look up each key's `failure_policy` from
  `self._ctx.cfg.mcp.mcp_servers[key].failure_policy` (the same config object
  `discover_all()` reads), not from `unavailable_servers` itself. This is a source of
  ambiguity the source Plan's Design section did not fully specify ("具体的な文言は実装
  時に確定する") — resolved here by reading from `ctx.cfg.mcp.mcp_servers`, which is
  already accessible on `self._ctx` at this point in `startup.py` (confirmed via Read
  that other lines in the same method, e.g. line 552, already do
  `self._ctx.cfg.mcp.mcp_servers`).
- Confirmed via Read (`tests/agent/test_startup.py`) and `rg "unavailable_servers|Excluded
  tools" tests/agent/test_startup.py` that no existing test currently asserts on this
  log line's content — this is a new test, not a modification of an existing one.

## Design decisions

- Change the log line from `{', '.join(sorted(unavailable_servers))}` to a
  per-server rendering that includes each server's `failure_policy`, e.g.: `", ".join(
  f"{key} ({self._ctx.cfg.mcp.mcp_servers[key].failure_policy})" for key in
  sorted(unavailable_servers))` — producing output like `"Excluded tools (unavailable):
  srv1 (disable-tool), srv2 (degraded)"`.
- Guard the dict lookup: if a key in `unavailable_servers` is somehow absent from
  `self._ctx.cfg.mcp.mcp_servers` (should not happen in practice, since
  `unavailable_servers` is derived from iterating that same dict in `discover_all()`),
  fall back to the bare key without a parenthetical rather than raising — use `.get(key)`
  with a `None`-safe format, not a direct `[key]` subscript, to avoid a `KeyError`
  crashing the readiness-summary log line itself.

## Alternatives considered

- Threading `failure_policy` values through `DiscoveryResult`/`RuntimeToolRegistry`
  instead of re-reading `ctx.cfg.mcp.mcp_servers` at log time: rejected — `cfg.mcp.
  mcp_servers` is already the single source of truth for this value and is already
  reachable from `startup.py` at this call site; adding a new field to
  `RuntimeToolRegistry`/`DiscoveryResult` to carry a value already available via `ctx.cfg`
  would be redundant plumbing for a log-line-only consumer.

## Implementation

### Target file
`scripts/agent/startup.py`

### Procedure
1. Replace the log-line construction at `scripts/agent/startup.py:565-568` per Design
   decisions, using a `.get(key)`-based lookup guarded against a missing config entry.
2. Add a test to `tests/agent/test_startup.py` that sets up a mocked
   `ctx.services_required.runtime_tools.unavailable_servers` (or the equivalent fixture
   pattern already used by nearby tests in this file — confirm the file's existing
   mocking convention before writing) containing one or more server keys, sets
   `ctx.cfg.mcp.mcp_servers` with matching `failure_policy` values, and asserts the
   rendered log line contains each key's `failure_policy` value.

### Method
Single log-line construction change plus one new test; no other logic in the
enclosing method changes.

### Details
- Do not change `degraded_keys`/`Degraded servers` (lines 550-556) — unrelated to this
  Requirement.

## Compatibility considerations

- Log-line format change only (adds `(failure_policy)` per server) — no change to any
  programmatic consumer, since this is a human-readable warning line
  (`self._view.write_warning(...)`/`logger.info(...)`), not a structured/parsed field.

## Security considerations

- Directly implements ADR-004 Decision #5's observability requirement — an operator
  relying on `disable-tool`/`degraded` for a `required=True` server now sees which
  policy was applied for each excluded server at startup, reducing the risk noted in the
  source Plan's Risks section (an operator not noticing a load-bearing server's
  unavailability).

## Rollback considerations

- Revert the log-line construction to the plain `sorted(unavailable_servers)` join and
  remove the new test.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/startup.py` | Unit | `PYTHONPATH=scripts uv run pytest tests/agent/test_startup.py -v` | New test passes; no existing test in the file regresses |

## Completion criteria

- The "Excluded tools (unavailable)" log line includes each excluded server's
  `failure_policy` value.
- A missing config entry for a key in `unavailable_servers` does not raise `KeyError`
  when rendering this log line.
- A new test in `tests/agent/test_startup.py` asserts the `failure_policy` values appear
  in the rendered line.

## Out of scope

- `scripts/agent/services/mcp_tool_discovery.py`'s decision logic — see the companion
  implementation procedure document for REQ-001.
- `degraded_keys`/`Degraded servers` log line.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirm this file's existing test-mocking convention for `ctx.cfg.mcp.mcp_servers`/`runtime_tools` before writing the new test | Pending | — | — | |
| 2 | Change the "Excluded tools (unavailable)" log line to include per-server `failure_policy` | Pending | — | — | |
| 3 | Add the new log-content test to `tests/agent/test_startup.py` | Pending | — | — | |
| 4 | Run the validation sequence (`rules/toolchain.md`) scoped to this file and its tests | Pending | — | — | |
| 5 | Documentation update | N/A | — | — | Not in scope for this file |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| Assumption | コンパニオン `mcp_tool_discovery.py` に `failure_policy` フィールドが未追加。`discovery_result` が `failure_policy` を持っていないため、ログ行への埋め込みが実行不可。手順書の前提と実際のコードに依存関係あり。 | No | 2026-08-25 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-002`, `REQ-003` (partial) — render applied `failure_policy` in the startup readiness log
- **Source issue**: `issues/20260823_adr004_failure_policy_unused_issue.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260825-133610_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260825-180630
- **Related target files**: `scripts/agent/startup.py`
