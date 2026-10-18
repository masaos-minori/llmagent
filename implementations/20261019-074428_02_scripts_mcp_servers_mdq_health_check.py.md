## Goal

Extract the dependency-collection logic currently inline inside `check_health()` in
`scripts/mcp_servers/mdq/health_check.py` into a reusable helper that returns
`(mdq_cfg, db_file_present, schema_error, schema_checked, index_stats)`, and refactor
`check_health()` to call it. This makes the logic available to the import-time posture build in
`mdq_server.py` without duplicating it, while keeping `/health` output byte-for-byte unchanged
(REQ-003 / AC-003).

## Scope

- **In-Scope**:
  - Extract the dependency-collection logic from `check_health()` into a reusable helper returning
    `(mdq_cfg, db_file_present, schema_error, schema_checked, index_stats)`.
  - Refactor `check_health()` to call the helper; confirm the `/health` response body is unchanged.
- **Out-of-Scope**:
  - Changing how MDQ computes or publishes its security posture on `/health`.
  - Moving the helper out of `health_check.py` (e.g. into `mdq_security_validation.py`).
  - Any `docs/*.md` change.

## Assumptions

- The extraction is purely structural (behavior-preserving): the same config load, DB probe,
  schema check, and index-stats collection run in the same order, producing the same five values.
- `build_mdq_posture()` is called with the same five arguments in both `check_health()` and the
  import-time build, so sharing the collector cannot change the posture.
- The existing `test_mdq_health*.py` suite covers `/health` and must still pass unchanged.

## Design decisions

- Keep the helper in `health_check.py` (not moved to `mdq_security_validation.py`) to respect the
  `mcp_servers → db, shared` import layer.
- The helper returns the five-value tuple exactly as the plan specifies; `check_health()` consumes
  it and reconstructs `deps` / `details` identically to before.
- The returned tuple's types match the current locals (`mdq_cfg: dict`, `db_file_present: bool`,
  `schema_error: tuple[str, str] | None`, `schema_checked: bool`,
  `index_stats: Mapping[str, object] | None`).

## Alternatives considered

- Duplicating the collection logic into the import-time gate — rejected: it would diverge from the
  published `/health` checks (the plan's stated reason for extraction) and risk drift.
- Moving the helper to `mdq_security_validation.py` — rejected: violates the import-layer rule.

## Implementation

### Target file

`scripts/mcp_servers/mdq/health_check.py`

### Procedure

1. Read the current `check_health()` body (lines ~113-160) to capture the exact collection order,
   the `deps` / `details` population, and the `try/except` handling.
2. Add a module-level helper `_collect_dependencies()` that performs the collection and returns the
   five-value tuple:
   ```python
       def _collect_dependencies() -> tuple[
           dict[str, object], bool, tuple[str, str] | None, bool, dict[str, object] | None
       ]:
           \"\"\"Load config and probe dependencies for MDQ health/posture.

           Shared by `check_health()` (the /health endpoint) and the import-time
           security-posture build in `mdq_server.py`. Returns
           `(mdq_cfg, db_file_present, schema_error, schema_checked, index_stats)`.
           \"\"\"
           mdq_cfg: dict[str, object] = {}
           db_file_present = False
           schema_error: tuple[str, str] | None = None
           schema_checked = False
           index_stats: dict[str, object] | None = None
           try:
               mdq_cfg = ConfigLoader().load(MDQ_OWN_CONFIG_FILE)
               db_path = str(mdq_cfg.get("db_path") or DEFAULT_DB_PATH)
               allowed_dirs = configured_allowed_dirs(mdq_cfg)
               _ = len(allowed_dirs)  # reserved for details reconstruction below
               db_file_present = Path(db_path).is_file()
               if not db_file_present:
                   ...
               else:
                   ...
           except (FileNotFoundError, PermissionError, KeyError, TypeError) as e:
               ...
           return mdq_cfg, db_file_present, schema_error, schema_checked, index_stats
   ```
   See the Method section for how `deps` / `details` are preserved.
3. Refactor `check_health()` to call the helper and reconstruct `deps` / `details` exactly as
   before, then call `build_mdq_posture()` with the returned five values:
   ```python
       def check_health() -> JSONResponse:
           \"\"\"Check mdq-mcp health and return appropriate response.\"\"\"
           deps: dict[str, str] = {}
           details: dict[str, object] = {"service": "mdq-mcp"}
           mdq_cfg, db_file_present, schema_error, schema_checked, index_stats = (
               _collect_dependencies()
           )
           # Reconstruct details from the returned values (see Method / Plan Gap).
           ...
           posture = build_mdq_posture(
               mdq_cfg, db_file_present, schema_error, schema_checked, index_stats
           )
           if deps:
               return _degraded_response(deps, details, posture)
           result: JSONResponse = make_health_response(deps, details, security=posture)
           return result
   ```
4. Run the existing `test_mdq_health*.py` suite and diff a representative `/health` response against
   the pre-change output to confirm AC-003.
5. Run `ruff` / `mypy` / `bandit` on the touched file; confirm clean.

### Method

- **Preserve `deps` / `details` exactly.** This is the central correctness concern (AC-003). The
  original `check_health()` populates `deps` (`db_file` / `config`) and `details`
  (`service`, `database`, `allowed_dirs_count`, `deny_all`, `index_stats`) during collection. Two
  faithful options:
  - **(a) Reconstruct in `check_health()`.** The helper returns only the five-value tuple;
    `check_health()` rebuilds `details` from the returned `mdq_cfg` (database path, `allowed_dirs`
    count/deny-all, and the `index_stats` merge) and rebuilds `deps` from the returned flags
    (`db_file_present` → `db_file` dep; `schema_error` → dep; a config exception → `config` dep).
  - **(b) Return `deps` / `details` too.** If reconstruction is error-prone, extend the helper's
    return to `(deps, details, *five_tuple)`; this deviates from the plan's stated five-value
    signature but is the lowest-risk way to guarantee an identical `/health` body. Prefer (a) to
    honor the frozen signature; choose (b) only if (a) cannot reproduce the exact output.
- **Keep the `try/except` semantics.** The helper catches the same
  `(FileNotFoundError, PermissionError, KeyError, TypeError)` and maps them to the same `deps["config"]`
  entry; the import-time build must see the same failure signal.
- **Do not reorder or alter the collection.** The DB probe, schema check, and index-stats
  collection run in the same order so the posture input is identical.

### Details

- `REQ-003`: the dependency-collection logic inside `check_health()` is extracted into a reusable
  helper shared by `/health` and the import-time posture build, with no behavior change to
  `/health`.
- **UNK-01:** not blocking; the single production construction site of `RagConfigImpl` is
  `resolve_rag_config`, which validates before construction. (retained placeholder — N/A here)

> **Plan Gap (scope decision for the Plan, not applied here):** the plan fixes the helper's return
> signature at the five-value tuple `(mdq_cfg, db_file_present, schema_error, schema_checked,
> index_stats)`, yet `check_health()` also needs `deps` and `details` to build the response. A
> five-value-only return forces `check_health()` to reconstruct both from the returned values. This
> is the highest-risk part of the change for AC-003; the implementer MUST diff the `/health` response
> before and after extraction and choose option (b) above if reconstruction cannot reproduce the
> exact body.

## Compatibility considerations

Behavior-preserving extraction. No change to `/health` output (AC-003), the posture computation, or
any public contract. The helper stays in `health_check.py`. No `docs/*.md` change.

## Security considerations

N/A: structural refactor only; no change to security-relevant behavior. The fail-closed enforcement
in `mdq_server.py` (added by the sibling document) is unaffected.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/mcp_servers/mdq/health_check.py` | Integration: `/health` output unchanged after extraction | `uv run pytest tests/mcp_servers/mdq/test_mdq_health*.py` | existing health tests pass unchanged |
| `scripts/mcp_servers/mdq/health_check.py` | Static — lint and type check | `uv run ruff check`, `uv run mypy --no-namespace-packages scripts/` | Clean (no new findings) |

## Completion criteria

- The dependency-collection logic lives in a reusable `_collect_dependencies()` helper returning the
  five-value tuple (AC-003).
- `/health` output is unchanged after the extraction (AC-003).
- Existing `test_mdq_health*.py` pass unchanged.

## Out of scope

Changing how MDQ computes or publishes its security posture on `/health`, moving the helper out of
`health_check.py`, and any `docs/*.md` change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Extract dependency-collection helper from `check_health()` | Pending | — | — | REQ-003; AC-003 |
| 2 | Phase 2a: Build MDQ posture once at import | Pending | — | — | REQ-002; `scripts/mcp_servers/mdq/mdq_server.py` |
| 3 | Phase 2b: Add `_enforce_posture_gate()` and call it in `__main__` | Pending | — | — | REQ-001; `scripts/mcp_servers/mdq/mdq_server.py` |
| 4 | Phase 3: Add `test_mdq_health_posture.py` | Pending | — | — | REQ-004; `tests/mcp_servers/mdq/test_mdq_health_posture.py` |
| 5 | Phase 4: Static checks, MDQ test suite, deploy confirmation | Pending | — | — | REQ-001..REQ-005 |

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
- **Requirement ID**: `REQ-003`
- **Source issue**: issues/20261018-191517_mcp002_mdq-mcp-server-lacks-pre-bind-fail-closed-security-posture-gate.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261018-222300_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-074428
- **Related target files**: scripts/mcp_servers/mdq/health_check.py
