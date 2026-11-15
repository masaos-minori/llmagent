## Goal

Replace `scripts/shared/http_transport.py`'s local `_WRITE_TOOLS` union with the imported canonical `ALL_SIDE_EFFECTING_TOOLS` (new), so its fail-closed write gate covers exactly the tools the dispatch layer deduplicates, including MDQ `index_paths`/`refresh_index`.

## Scope
**Release unit**: N/A: not part of a release unit

- Covers `REQ-003`: the fail-closed gate derives membership from the canonical set instead of a local union.

## Assumptions
- `ALL_SIDE_EFFECTING_TOOLS` is created by sibling procedure `20261115-192353_01_scripts_shared_tool_constants.py.md`; the current `_WRITE_TOOLS` union (lines 36-45) mirrors `dispatch.py` and excludes MDQ, so delegation adds only `index_paths`/`refresh_index`.
- The canonical name resolves from the earlier-`seq` sibling; this document does not create it.

## Design decisions
- Keep the module-level name `_WRITE_TOOLS` and assign it the canonical set directly (`_WRITE_TOOLS = ALL_SIDE_EFFECTING_TOOLS`), so the two gate call sites (lines 246 and 304) stay unchanged; only the source of membership moves.

## Alternatives considered
- N/A: single obvious delegation mirroring `dispatch.py`; the Plan fixes importing the canonical set.

## Implementation
### Target file
- `scripts/shared/http_transport.py`

### Procedure
1. In the `from shared.tool_constants import (...)` block (lines 16-25), drop the now-unused category imports (`CICD_WRITE_TOOLS`, `DELETE_TOOLS`, `GIT_WRITE_TOOLS`, `GITHUB_DANGEROUS_TOOLS`, `GITHUB_WRITE_TOOLS`, `RAG_WRITE_TOOLS`, `SHELL_TOOLS`, `WRITE_TOOLS`) and import `ALL_SIDE_EFFECTING_TOOLS` instead. These eight names are referenced only inside the union being removed (lines 37-44).
2. Replace `_WRITE_TOOLS: frozenset[str] = frozenset(...)` (lines 36-45) with `_WRITE_TOOLS: frozenset[str] = ALL_SIDE_EFFECTING_TOOLS`. Update the surrounding comment (lines 32-35) to state the gate now reads the shared canonical set rather than mirroring `dispatch.py`.

### Method
- Behavior-preserving for all currently-covered tools; adds MDQ writes to the fail-closed gate. Gate call sites at lines 246 and 304 are untouched.

### Details
- The expansion (gate now covers `index_paths`/`refresh_index`) is the intended behavior change: a write failure on an MDQ tool is now fail-closed instead of retried, consistent with `dispatch.py` dedup and `tool_policy.py`'s existing static classification.

## Compatibility considerations
- Import cleanup required: leaving the eight category imports unused trips `ruff` F401; removed in step 1. Import direction unchanged (`shared/` internal).
- Pre-send safe-error handling (`_PRESEND_SAFE_ERRORS`, lines 50+) is unaffected.

## Security considerations
- Aligns with ADR-004 (fail-closed on writes): a failed MDQ write is no longer classified retryable at the transport layer, preventing a duplicate side effect on retry.

## Rollback considerations
- Revert the commit: restore the union and the eight category imports.

## Validation plan
- `pytest` transport tests under `tests/` (e.g. `tests/shared/test_http_transport.py`) — an MDQ write failure is classified fail-closed after the change; pre-send errors still retry safely; no new failures.
- `uv run ruff check scripts/shared/http_transport.py` — no unused imports; `uv run mypy --no-namespace-packages scripts/` clean.

## Completion criteria
- `scripts/shared/http_transport.py` no longer defines a local category union; `_WRITE_TOOLS` is `ALL_SIDE_EFFECTING_TOOLS`.
- A write failure on `index_paths`/`refresh_index` is fail-closed at the gate.

## Out of Scope
- Changing retry classes or `_PRESEND_SAFE_ERRORS`; editing `tool_constants.py` (seq 01) or `dispatch.py` (seq 02).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Import `ALL_SIDE_EFFECTING_TOOLS`, drop unused category imports, set `_WRITE_TOOLS` to canonical | Pending | — | — | REQ-003 |
| 2 | Add/extend transport test asserting MDQ write failure is fail-closed | Pending | — | — | REQ-003, REQ-005 |
| 3 | Run validation sequence (`rules/toolchain.md`) | Pending | — | — | pytest + ruff + mypy |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: no doc row in this Plan |

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
- **Requirement ID**: `REQ-003` (http_transport derives the fail-closed write gate from the canonical set)
- **Source issue**: `issues/20261111-163800_sideeffect001_side-effect-classification-central.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261115-052032_sideeffect001_side-effect-classification-central.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261115-192353
- **Related target files**: `scripts/shared/http_transport.py`
