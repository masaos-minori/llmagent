## Goal
- Give every server a way to put the dedup metrics block into its health `details` without giving any server a second status path (REQ-004 publish the metrics through the existing health `details` block).

## Scope
**Release unit**: health exposure
- Adds one public helper, `dedup_health_details()` (new), to `scripts/mcp_servers/health_response.py`.
- Keeps `make_health_response` exactly as it is: the same payload keys, defaults, status-code selection, signature, and the defensive `details` copy.
- Degradation is silent-by-design: when the dispatcher has no store or config, or the read fails, the helper returns an empty dict and logs a warning.
- Out of scope: the handler wirings themselves (rows 10-17), the metrics read (row 05), and the payload assertions (row 20).

## Assumptions
- The store and config are read from the dispatcher's module globals — `_dedup_store` and `_dedup_config` — which `configure_dedup()` sets at bootstrap; they are read through `getattr` on the imported module, because a module-level name import would capture `None` at import time.
- The dispatcher import is function-local: `scripts/mcp_servers/dispatch.py` is imported by the server bootstrap that also imports this module, so deferring the import to the call keeps module import order unchanged and no import-time cycle can form.
- Importing `collect_dedup_metrics` from the `shared.mcp_dedup` facade is allowed by the import-layer contract (`mcp_servers` may import `shared`), the same direction the module already uses for its `shared.security.posture_contract` import.

## Design decisions
- Read the existing dispatcher globals instead of adding a public accessor to `scripts/mcp_servers/dispatch.py`: `dispatch.py` is a Reference File of this Plan, not an Implementation Target Files row, and it is 3 bytes under the 24576 B size gate, so it gains no code.
- Mirror `_purge_once` (line 219 of `scripts/mcp_servers/dispatch.py`) for degradation: catch `(sqlite3.Error, OSError)`, log a warning, and return an empty dict, so `/health` never fails because the store is busy or broken.
- The helper returns `{"dedup": ...}` or `{}` — it never mutates the dict a caller passes to `make_health_response`, which already copies `details`.

## Alternatives considered
- Adding the metrics block inside `make_health_response` itself: rejected, the payload key set is pinned by `BASE_KEYS` in `tests/mcp_servers/test_health_response.py` and every server would change at once.
- A new status endpoint: rejected by the Plan's out-of-scope list and the one-execution-route invariant.

## Implementation
### Target file
`scripts/mcp_servers/health_response.py`

### Procedure
1. Add module-level `logging` and `sqlite3` imports and a module `logger`, matching the shape the other `mcp_servers` modules use.
2. Add `dedup_health_details()` (new), a public function returning `dict[str, object]`, placed after `make_health_response`.
3. Inside it, import `mcp_servers.dispatch` locally, then read `getattr(dispatch, "_dedup_store", None)` and `getattr(dispatch, "_dedup_config", None)`.
4. If either is `None`, return `{}`. Otherwise call `collect_dedup_metrics` with the store and config and return `{"dedup": ...}`; wrap that call in `except (sqlite3.Error, OSError)` returning `{}` after `logger.warning`.

### Method
- No change to `make_health_response`: its payload keys `status`, `ready`, `liveness`, `restart_recommended`, `operator_action_required`, `dependencies`, `details` (plus `security` when a posture is supplied), its `200` and `503` selection, and its argument defaults all stay as they are, including the defensive copy at line 53.
- Handlers compose the block themselves: a handler calls `dedup_health_details()` and merges it into the `details` dict it already passes, so the `service` key each server publishes stays untouched.

### Details
- The helper is additive for the tests that assert `details` by key membership and only additive-content for the three endpoint tests that assert the whole dict; those tests are separate Plan rows (rows 20-24), not this document.
- `collect_dedup_metrics` and the `METRICS_SCHEMA_VERSION` constant arrive through `scripts/shared/mcp_dedup.py` (row 06), so this module gains no `shared.mcp_dedup_metrics` import of its own.
- The helper never issues a write: everything it returns comes from the read-only path row 05 defines.

## Compatibility considerations
- `tests/mcp_servers/test_health_response.py` asserts `set(body) == BASE_KEYS` and `details == {}` for a bare call; because this row changes no payload key and adds no default argument, those assertions keep passing unchanged and the new assertions belong to row 20.
- `tests/mcp_servers/test_mcp_dispatch.py` pins the dispatcher's degradation behaviour, which this row mirrors without modifying.
- Servers that never call `configure_dedup()` get `{}` here, which is the same `details` content they return today.

## Security considerations
- The block carries store path and counts only — no row payloads, keys, or owner ids — so `/health` does not become a data read endpoint.
- The read-only helper cannot mutate the store, and its failure path returns an empty dict rather than an exception that would leak internals into the response.

## Rollback considerations
- Revert the commit: `make_health_response` is untouched, so a revert removes the helper and leaves every health payload exactly as before.

## Validation plan
- `uv run pytest tests/mcp_servers/test_health_response.py tests/shared/test_mcp_dedup.py` (unit, expect Pass).
- `uv run python tools/run_validation_gates.py` for the diff, plus the full sequence in `rules/toolchain.md`.

## Completion criteria
- With a configured store the helper returns a `dedup` block containing the metrics fields; with no store, no config, or a failing read it returns `{}` and logs a warning without raising.
- `make_health_response` output for a call without the new block is byte-identical to today.

## Out of Scope
- The 10 handler wirings (rows 10-17), the metrics module (row 05), the facade re-export (row 06), and the per-server `details` test extensions (rows 20-24).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement `dedup_health_details()` (new) per Procedure/Method/Details | Completed | — | 20261123-222910 | Changed: scripts/mcp_servers/health_response.py (dedup_health_details new, module logger, logging and sqlite3 imports). make_health_response unchanged: same payload keys, defaults, status-code selection, signature, defensive details copy. Store and config are read through the imported dispatch module with getattr, and the dispatcher import is function-local so module import order is unchanged. Degradation returns an empty dict and logs a warning; the returned dict is new so the caller's details is never mutated. |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261123-222916 | No test step: the payload assertions belong to `tests/mcp_servers/test_health_response.py` (row 20) and `tests/shared/test_mcp_dedup.py` (row 18) This member Step 3e: ruff format/check pass, run_validation_gates.py fast mode all applicable gates Pass, lint-imports 6 contracts kept, mypy clean across scripts/, bandit clean on this file. tests/mcp_servers/test_health_response.py 10 passed unchanged, and the check_doc_symbols warning for dedup_health_details is resolved by this row. Full suite runs once at end of the release unit. |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-004 (publish the read-only metrics through the existing health `details` block)
- **Source issue**: issues/20261120-115844_mcpdl005_retention-capacity-monitoring.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-120131_mcpdl005_retention-capacity-monitoring.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-144326
- **Related target files**: `scripts/mcp_servers/health_response.py`