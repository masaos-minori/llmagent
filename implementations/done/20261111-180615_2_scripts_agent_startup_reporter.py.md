## Goal
Remove the `failure_policy` lookup from the readiness warning in `scripts/agent/startup_reporter.py` so unavailable servers are listed by key only, and rename the companion test in `tests/agent/test_startup.py` that is named after the removed field (`REQ-001`, Plan Phase 1).

## Scope
**Release unit**: N/A: not part of a release unit

- **Target file**: `scripts/agent/startup_reporter.py` (frozen-table row 2).
- **Companion test row**: `tests/agent/test_startup.py` (frozen-table row 3) is covered by this document and gets no document of its own: it exists only to exercise row 2's `REQ-001` readiness behavior, and its test name would reference a removed symbol if left unchanged.

## Assumptions
- A-2 (from the Plan): the warning change from `srv (fail-fast)` to `srv` affects no parser or document — `tests/agent/test_startup.py` asserts only the prefix and the server names, `tests/agent/test_startup_reporter.py` names no policy text, and `docs/` never quotes the suffix (verified 2026-11-11).

## Design decisions
- Keep the `if policy is not None` conditional removal simple: build `parts` from the keys directly (`parts = sorted(unavailable_servers)` then join), matching the frozen row "lists unavailable servers by key only".
- Rename the test rather than delete it: its assertions (prefix, `srv1`, `srv2`) remain valid coverage of the readiness line.

## Alternatives considered
- Keep `getattr(..., "failure_policy", None)` as a harmless no-op — rejected: the whole `REQ-001` goal is to leave no reference to the removed field.
- Delete the companion test — rejected in the Plan: the test asserts behavior that still exists (servers listed by key).

## Implementation
### Target file
`scripts/agent/startup_reporter.py`; companion edit in `tests/agent/test_startup.py`.

### Procedure
1. In the `if unavailable_servers:` block (lines 119-128), remove the `cfg_entry`/`policy` lookups and the `f"{key} ({policy})"` formatting; list sorted keys only.

### Method
Direct deletion of the three-line policy branch; the sort order of keys is preserved (`sorted(unavailable_servers)` remains).

### Details
Before (lines 119-128):

```python
        if unavailable_servers:
            parts = []
            for key in sorted(unavailable_servers):
                cfg_entry = self._ctx.cfg.mcp.mcp_servers.get(key)
                policy = getattr(cfg_entry, "failure_policy", None)
                if policy is not None:
                    parts.append(f"{key} ({policy})")
                else:
                    parts.append(key)
            lines.append(f"  Excluded tools (unavailable): {', '.join(parts)}")
```

After:

```python
        if unavailable_servers:
            parts = sorted(unavailable_servers)
            lines.append(f"  Excluded tools (unavailable): {', '.join(parts)}")
```

### Companion test files
- `tests/agent/test_startup.py`
  - Procedure: rename `test_excluded_tools_log_includes_failure_policy` to `test_excluded_tools_log_lists_unavailable_server_keys` (new); assertions unchanged (prefix, `srv1`, `srv2`).
  - Validation: `uv run pytest tests/agent/test_startup.py -v` passes with the renamed test; `rg -n "failure_policy" tests/agent/test_startup.py` returns no hit.

## Compatibility considerations
- Operator-visible change: the readiness warning line changes from `srv (fail-fast)` to `srv` (Plan Design "Operator-visible change"); state it in the commit message.
- `tests/agent/test_startup_reporter.py` references no policy text and must keep passing unchanged.
- Depends on document `20261111-180615_1` removing the field itself; until that lands, the `getattr` default would simply always yield `None`, so the two documents land in one commit without an ordering requirement inside the cycle.

## Security considerations
No security surface change (warning text formatting only).

## Rollback considerations
Single-commit revert restores the suffix; no persisted state, no config change.

## Validation plan
- `uv run pytest tests/agent/test_startup_reporter.py tests/agent/test_startup.py -v` — pass; unavailable servers listed by key (Plan Validation plan row 2).
- `rg -n "failure_policy" scripts/agent/startup_reporter.py tests/agent/test_startup.py` — no hit.
- `uv run ruff check scripts/agent/startup_reporter.py tests/agent/test_startup.py`; `uv run mypy --no-namespace-packages scripts/` — no new findings.

## Completion criteria
- No `failure_policy` reference remains in the two edited files; the renamed test passes; the AC-1 example output lists keys only.
- All Validation plan commands pass.

## Out of Scope
- `scripts/shared/mcp_config.py` field/enum removal (document 1) and the documentation bullet (document 4).
- Any other `ReadinessReporter` output lines (degraded servers, unreachable count).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261111-184859 | 20261111-184950 | includes the companion rename in tests/agent/test_startup.py policy lookup removed; test renamed; changed: scripts/agent/startup_reporter.py, tests/agent/test_startup.py; Details citation corrected to 119-128 |
| 2 | Add or update tests per Validation plan | Completed | 20261111-184950 | 20261111-185004 | rename only, no new tests 46 targeted tests pass incl. renamed test; rename only |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261111-190102 | ruff/mypy/lint-imports/bandit/ref-table/module-size pass; full suite 12111 passed; diff-cover 100% |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261111-190102 | document 4 owns the docs change N/A: no docs/00_index.md task-scope mapping for scripts/agent/startup_reporter.py; docs never quote the suffix (rg); bullet removal owned by document 4 |

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
- **Requirement ID**: `REQ-001` (Plan rows AC-1, AC-2)
- **Source issue**: issues/20261111-163923_compat009_workflow-legacy-compat-removal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-170504_compat009_workflow-legacy-compat-removal.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261111-180615
- **Related target files**: `scripts/agent/startup_reporter.py`, `tests/agent/test_startup.py` (companion row)