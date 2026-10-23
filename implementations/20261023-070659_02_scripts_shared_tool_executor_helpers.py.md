## Goal

Correct the `tool_hash_key` docstring in `scripts/shared/tool_executor_helpers.py:41` so it describes what the function actually does (an MD5 identity for a failed call, explicitly NOT a cache key) instead of asserting a cache-key format that no code in `scripts/shared/` builds (REQ-006).

## Scope

Only `scripts/shared/tool_executor_helpers.py`: the `tool_hash_key` docstring at `:41`. No other file.

## Assumptions

- The "NOT for cache keys" contrast is load-bearing for readers who confuse this with the server-side cache, so the corrected docstring keeps that contrast rather than dropping it.
- The function body (`hashlib.md5` over `f"{name}:{_json_dumps(args)}"`) is correct and stays unchanged.

## Design decisions

- Replace only the false clause "Cache keys use plain string concatenation: `f'{name}:{json_dumps(args)}'`". State that the hash identifies a failed call and, if the real cache is referenced, that it is keyed by the caller's idempotency key plus tool name plus normalized argument hash (REQ-006, AC-5).
- Leave the function signature and body untouched — only the docstring text changes.

## Alternatives considered

- Rewriting the whole docstring block or moving the description elsewhere would add churn with no benefit; the false sentence is a single clause, so in-place substitution is sufficient.

## Implementation
### Target file
`scripts/shared/tool_executor_helpers.py`

### Procedure
1. Rewrite the cache-key-format clause in the `tool_hash_key` docstring (`:41`) (REQ-006).

### Method
- Locate the docstring: `grep -n "Cache keys" scripts/shared/` should currently match `:41`; after the edit it must return nothing (AC-5).
- Confirm the real cache location the corrected wording points at: `scripts/mcp_servers/dispatch.py:101-106`, `:122-129` (keyed by idempotency key), and the failed-call consumer `scripts/agent/tool_runner.py:237`.

### Details
- Current `:41`: `"...used for failed-call tracking (NOT for cache keys). Cache keys use plain string concatenation: f'{name}:{json_dumps(args)}'."`
- New: keep "`...used for failed-call tracking (NOT for cache keys)`", then describe the identity as the MD5 over `f"{name}:{json_dumps(args)}"` and, if the cache is mentioned, that the real cache lives server-side (`dispatch.py`) and is keyed by the caller's idempotency key plus tool name plus normalized argument hash. Do NOT present any client-side cache-key format (REQ-006, AC-5).

## Compatibility considerations
N/A: the change is a docstring-only clarification; no public contract or other file depends on the old wording.

## Security considerations
N/A: no security impact. The `hashlib.md5 ... usedforsecurity=False` (`# nosec B324`) body is unchanged.

## Rollback considerations
Revert the single commit.

## Validation plan
- `grep -rn "Cache keys" scripts/shared/` returns nothing (AC-5).
- `grep -n "tool_hash_key" -A2 scripts/shared/tool_executor_helpers.py` describes failed-call identity, not a cache-key format (AC-5).
- `uv run pytest tests/shared/test_tool_executor_helpers.py tests/agent/test_tool_loop_guard.py tests/agent/test_tool_runner.py -q` passes unmodified (REQ-006).
- `git diff --stat` lists exactly `scripts/shared/tool_executor_helpers.py` (AC-7).

## Completion criteria
The `tool_hash_key` docstring states no client-side cache-key format and correctly describes the failed-call identity (and, if referenced, the server-side cache keyed by idempotency key).

## Out of Scope
`scripts/agent/tool_runner.py`, `scripts/agent/tool_loop_guard.py`, `scripts/mcp_servers/dispatch.py`, `tests/shared/test_tool_executor_helpers.py`, and all `docs/*.md` — byte-identical.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change in Implementation > Procedure/Method/Details (docstring rewrite) | Pending | — | — | REQ-006 |
| 2 | Add or update tests per Validation plan | N/A | — | — | No new test module: no behaviour changes |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | acceptance greps, existing helper suites, git diff --stat |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | No `docs/*.md` edit in scope |

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
- **Requirement ID**: REQ-006, REQ-008
- **Source issue**: `issues/20261021-093421_doc001-module-docstrings-name-nonexistent-components.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-024105_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-070659
- **Related target files**: `scripts/shared/tool_executor_helpers.py`
