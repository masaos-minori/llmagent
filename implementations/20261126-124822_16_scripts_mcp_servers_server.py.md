## Goal
- Correct the stale "inert until the set is defined" docstring of the HTTP idempotency boundary, and sweep the real `ALL_SIDE_EFFECTING_TOOLS` through that boundary in tests (REQ-001, REQ-006).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the docstring of `_idempotency_key_middleware` in `scripts/mcp_servers/server.py` (no logic change) and its test companion.
- Out of scope: the middleware behavior, which already rejects keyless side-effecting calls with 422.

## Assumptions
- Verified in Step 3a: the docstring says the boundary is inert until a canonical set is defined, while `ALL_SIDE_EFFECTING_TOOLS` is a non-empty union of the write, delete, git, RAG, MDQ, CI/CD, GitHub, and shell sets (`server.py:150-177`; `scripts/shared/tool_constants.py:218-228`). The `if not ALL_SIDE_EFFECTING_TOOLS` short-circuit is behavior-neutral (with an empty set no tool name could match), so no code change is needed.
- Existing boundary tests inject a synthetic set (`_SIDE_EFFECTING = {"shell_run", "delete_document"}`) and use `shell_run` for the per-app check (`test_server_idempotency_boundary.py:34,253-262`), so the real set is never swept; the module docstring of that test also says the canonical set is not present yet.
- `server.py` is 21580 B, below the 24576 B module size gate; a docstring edit does not change that materially.

## Design decisions
- Docstring-only change to the production module; the sweep lives in the test companion and does not monkeypatch the set.

## Alternatives considered
- Remove the inert short-circuit: rejected, it is behavior-neutral and the change would touch logic for no gain.

## Implementation
### Target file
`scripts/mcp_servers/server.py`

### Procedure
1. In the docstring of `_idempotency_key_middleware`, replace the sentence stating that the boundary is inert until the canonical set is defined with a statement that the boundary consults the non-empty canonical set `ALL_SIDE_EFFECTING_TOOLS` from `shared.tool_constants`, and that the empty-set short-circuit is only a fast path with no behavioral effect.
2. Make no other edit to the function or the module.

### Method
- Keep the docstring format of the surrounding functions (summary line, then paragraphs).

### Details
- A docstring edit must not change any line outside the middleware's docstring.

### Companion test files
- `tests/mcp_servers/test_server_idempotency_boundary.py`
  - Procedure: update the module docstring (the canonical set exists); add a class that does not monkeypatch the set: assert the real set is non-empty, and for each tool in the sorted real set post `{"name": <tool>}` to the synthetic app and to one real app with no key and with a whitespace key, asserting 422; add a valid-key control per app showing the request passes the boundary; keep the existing tests that inject a synthetic set.
  - Validation: `uv run pytest tests/mcp_servers/test_server_idempotency_boundary.py`.

## Compatibility considerations
- No behavior change; the test additions only widen coverage.

## Security considerations
- The sweep proves no side-effecting tool bypasses the HTTP key requirement; no secret is involved beyond the existing test auth header.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/test_server_idempotency_boundary.py`; `uv run ruff format` and `uv run ruff check` on both files; `uv run mypy`; `wc -c scripts/mcp_servers/server.py` below 24576; then the sequence in `rules/toolchain.md`.

## Completion criteria
- The docstring matches the code; every tool of the real set is rejected without a key through the boundary; the existing boundary tests pass; all validation commands pass.

## Out of Scope
- Middleware logic, other docstrings, and documentation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Correct the docstring described in Implementation > Procedure | Pending | — | — | |
| 2 | Add the companion tests, then confirm they pass | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (keyless rejection over the real set, HTTP path), `REQ-006` (stale docstring corrected)
- **Source issue**: issues/20261119-141105_mcpdd001_dedup-keyless-config-gate.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-113156_mcpdd001_dedup-keyless-config-gate.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-124822
- **Related target files**: `scripts/mcp_servers/server.py`, `tests/mcp_servers/test_server_idempotency_boundary.py`
