## Goal
- Bound the `args_preview` field written by both agent-side audit writers in `scripts/agent/tool_audit.py` with one documented size cap and a structural truncation marker (`REQ-001` helper and cap, `REQ-002` both writers, `REQ-003` event shape kept, `REQ-004` marker distinct from masking).

## Scope
- Add one module constant and one private helper, and change the two `args_preview=masked` assignments (lines 58 and 169 at time of writing).
- No change to `scripts/agent/shared/models.py`, `scripts/shared/logger.py`, or any function signature.

## Assumptions
- Confirmed 2026-10-24: `audit_approval()` and `audit_tool_exec()` each compute `masked = mask_args(...)` and then set `args_preview=masked`; `_json_dumps` is imported from `shared.json_utils` (line 14) and returns `str`.
- `scripts/agent/tool_audit.py` is 7306 B, far under the 20480 B module gate (`tools/check_module_size.py`).
- The tests (row `02`) are written first per Plan Phase 1 and fail until this row lands; `code-implementation` MAY run row `02` before this row.

## Design decisions
- Cap is a character count of the serialized preview string; the value is a module constant `AUDIT_ARGS_PREVIEW_MAX_CHARS` (new) set to 1500, not `agent.toml` config (Plan Assumptions).
- Mask first, bound second; the envelope is a dict so `args_preview: dict[str, object]` stays valid.

## Alternatives considered
- Capping in `shared/logger.py` was rejected: the logger is shared with MCP-side and gateway writers where a bound would be wrong.
- A `[tool]` config key was rejected to keep `/opt/llm/config/agent.toml` out of scope.

## Implementation
### Target file
`scripts/agent/tool_audit.py`

### Procedure
1. Add the module constant `AUDIT_ARGS_PREVIEW_MAX_CHARS` (new) `= 1500` below the imports.
2. Add the private helper `_bounded_preview` (new) taking `masked: dict` and returning `dict`: serialize with `_json_dumps`; if `len(serialized) <= AUDIT_ARGS_PREVIEW_MAX_CHARS` return `masked` unchanged; otherwise return `{"preview": serialized[:AUDIT_ARGS_PREVIEW_MAX_CHARS], "truncated": True}`.
3. Replace both `args_preview=masked` with `args_preview=_bounded_preview(masked)` (new call).

### Method
- Place the helper next to `_extract_resource_scope`; give it a one-line English docstring in the file's style.
- Do not log or print from the helper.

### Details
- `masked` values are JSON-serializable (they already go through `_json_dumps` in the writers), so the helper adds no new failure mode; the extra serialization cost applies per audit row only.
- Typed signature `masked: dict[str, object]` is acceptable if it matches `mask_args`'s return annotation; keep mypy clean.

## Compatibility considerations
- Payloads at or under 1500 chars (all measured rows are 134 chars) pass through byte-for-byte; only oversized rows change shape.
- No repository code reads `args_preview` sub-keys (grep 2026-10-24); the event stays one JSON line.

## Security considerations
- Truncation happens after masking, so a retained prefix never contains an unmasked configured field; the `truncated` boolean keeps a reduced row distinguishable from a masked value.

## Rollback considerations
N/A: revert the commit; no persisted state depends on the envelope.

## Validation plan
- `uv run pytest tests/agent/test_tool_audit.py tests/agent/test_tool_approval_preflight.py tests/agent/test_audit_log_format.py -q`
- `rg -n "args_preview" scripts/` shows both writers going through `_bounded_preview` (new).
- `uv run ruff format scripts/agent/tool_audit.py`, `uv run ruff check scripts/agent/tool_audit.py`, `uv run mypy --no-namespace-packages scripts/`, `uv run bandit scripts/agent/tool_audit.py`, `PYTHONPATH=scripts uv run lint-imports`.

## Completion criteria
- An oversized payload is stored as `{"preview": <=1500 chars, "truncated": true}`; a payload at the cap is stored unchanged; both writers use the helper; existing audit tests pass unchanged.

## Out of Scope
- Masking rules and `masked_fields` defaults, approval-preview behavior, audit-log retention, MCP-side audit records.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the constant and `_bounded_preview` (new) helper | Completed | — | 20261025-002448 |  |
| 2 | Route both `args_preview` assignments through the helper | Completed | — | 20261025-002448 |  |
| 3 | Run the targeted audit tests | Completed | — | 20261025-002448 |  |
| 4 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261025-002448 |  |

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
- **Requirement ID**: `REQ-001` (cap constant and helper), `REQ-002` (both writers), `REQ-003` (event shape kept), `REQ-004` (marker distinct from masking)
- **Source issue**: `issues/20261024-124138_tool005-args-preview-is-written-to-the-audit-log-unbounded.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261024-221315_args-preview-is-written-to-the-audit-log-unbounded.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261024-235311
- **Related target files**: `scripts/agent/tool_audit.py`