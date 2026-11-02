# Let denial results through the audit early return

## Goal

Narrow the `audit_tool_exec` early return in `scripts/agent/tool_audit.py` so a denied result
(`error_type == "denied"`) is audited even with empty `mcp_request_id` and `source`, keeping the
no-op case for every other empty-identity call (Plan REQ-001 denial audited, REQ-002 no-op kept).

## Scope

- Add a module constant `_ERROR_TYPE_DENIED = "denied"` (new) in `tool_audit.py`.
- Change the guard at `tool_audit.py:194` (re-verified 2026-11-02; shifted from the `:173` cited
  at plan time by the assertaudit001 landing) from
  `if not mcp_request_id and not source:` to
  `if not mcp_request_id and not source and error_type != _ERROR_TYPE_DENIED:` — same position,
  before the `workflow_id` check.
- Nothing else: `source if source else "agent"` default (:213), event fields, and all other
  functions untouched; no schema change.

## Assumptions

- Verified 20261102: `_denied_result` (`repository_gateway.py:35-42`) sets `error_type="denied"`
  with `request_id=""`; the only production call site (`tool_runner.py:281-290`) passes
  `result.error_type` and `source=result.source` (empty for denied results), so denied writes
  currently hit the early return and are never audited (the Issue's defect).
- The literal `"denied"` in `_denied_result` stays as-is (Plan Design); the end-to-end test in
  `tests/agent/test_repository_gateway.py` pins the two values together.
- Batch order: assertaudit001 lands first (adjudication D3) — its skip-and-warn helper call sits
  after this narrowed guard, so a denial with no `workflow_id` warns and skips (REQ-004). This row
  must not disturb that position.

## Design decisions

- `ApprovalDecisionType.DENIED` not reused (Plan Design): it names an approval decision, not a
  result `error_type`; one module constant names the value once instead of a repeated literal.
- Removing the guard outright was rejected (Plan Design): it also skips cache/empty results by design.

## Alternatives considered

- Setting `source="agent"` in `_denied_result` — rejected (Plan Design): changes a result contract
  and leaves the audit function blind to future source-less denials.

## Implementation
### Target file
`scripts/agent/tool_audit.py`

### Procedure
Two edits: constant near `AUDIT_ARGS_PREVIEW_MAX_CHARS` (:28), and the guard condition at :194.

### Method
```python
_ERROR_TYPE_DENIED = "denied"
...
    if not mcp_request_id and not source and error_type != _ERROR_TYPE_DENIED:
        return
```

### Details
- Pure string comparison; cannot raise (Plan failure path).
- Event field set unchanged: `error_type="denied"`, `is_error` as passed, `mcp_request_id` empty,
  `source` defaults to `"agent"` (:213).

## Compatibility considerations

- All pre-existing calls with non-empty `mcp_request_id` or `source` are value-identical; the
  non-denied empty-identity case still writes nothing (REQ-002 / AC-2).
- `bandit` B101 findings on this file stay until assertaudit001 (Plan baseline note).

## Security considerations

- Closes an audit blind spot: policy-denied write attempts currently leave no `tool_exec` record.

## Rollback considerations

- N/A: revert the commit; reverts hide denials again.

## Validation plan

- `uv run pytest tests/agent/test_tool_audit.py tests/agent/test_tool_approval_preflight.py` —
  new tests (row 02) are red before this row lands.
- `uv run pytest tests/agent/test_repository_gateway.py tests/agent/test_tool_runner.py` — the
  gateway-driven denial test passes after this row (row 03).
- `uv run ruff format`, `uv run ruff check`, `uv run mypy`, `uv run lint-imports`,
  `uv run bandit -r scripts/ -c pyproject.toml`, `uv run python tools/check_module_size.py`,
  `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90`.

## Completion criteria

- `audit_tool_exec(ctx, tool, args, True, "", "denied", source="")` writes exactly one `tool_exec`
  record with `error_type="denied"`; the same call with `error_type` empty writes nothing; the
  gateway denial path produces exactly one audit record (row 03).

## Out of Scope

- Tests (rows 02-03); the `workflow_id` guard rewrite (assertaudit001's document); no docs row in
  this Plan's target table.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `_ERROR_TYPE_DENIED` (new) and narrow the early-return condition | Completed | 20261102-180955 | 20261102-184339 | After rows 02-03's red tests land; after assertaudit001 lands (batch order) _ERROR_TYPE_DENIED added (:28) + guard narrowed (:195); 217 targeted tests green |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261102-180955 | 20261102-184339 | Deploy hand-off is Plan Phase 3, user decision ruff/mypy/lint-imports/bandit -ll/check_module_size pass; full suite 11354 passed; diff-cover 100%; pre-existing mypy unused-ignore in scripts/rag/ingestion (4) noted as out of scope |

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
- **Requirement ID**: REQ-001 (denial audited despite empty ids), REQ-002 (no-op case preserved)
- **Source issue**: issues/20261003-180330_toolaudit001_audit-drops-denied-gateway-tool-calls.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261101-141718_toolaudit001_audit-drops-denied-gateway-tool-calls.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-132702
- **Related target files**: scripts/agent/tool_audit.py