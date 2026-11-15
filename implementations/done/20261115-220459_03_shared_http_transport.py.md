## Goal

Derive `scripts/shared/http_transport.py`'s fail-closed write gate
(`_WRITE_TOOLS`) from the imported canonical set `ALL_SIDE_EFFECTING_TOOLS`
instead of a local union, so the transport write-failure gate covers the MDQ
`index_paths`/`refresh_index` tools. (`REQ-003`)

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- `ALL_SIDE_EFFECTING_TOOLS` (row 01) equals today's `_WRITE_TOOLS` union plus
  `MDQ_WRITE_TOOLS`; replacing the local union with the import is
  behavior-preserving except that it extends the fail-closed gate to MDQ writes.
- The gate is ADR-004 fail-closed-on-writes; expanding it to MDQ matches
  `tool_policy.py`'s existing static classification.

## Design decisions

- Replace the module-level `_WRITE_TOOLS` frozenset with a reference to the
  imported `ALL_SIDE_EFFECTING_TOOLS`.

## Alternatives considered

- **Keep the local union and add `MDQ_WRITE_TOOLS`.** Rejected: second local
  reconstruction; the canonical set is the one source.

## Implementation
### Target file
`scripts/shared/http_transport.py`

### Procedure
1. Add `ALL_SIDE_EFFECTING_TOOLS` to the
   `from shared.tool_constants import (...)` block (lines 16-25).
2. Replace the `_WRITE_TOOLS` frozenset (lines 36-45) with a reference to the
   imported set, e.g. `_WRITE_TOOLS = ALL_SIDE_EFFECTING_TOOLS`.
3. Update the comment above the definition to cite the canonical set instead of
   "Mirrors scripts/mcp_servers/dispatch.py's `_write_tools`".

### Method
Delete the `frozenset(WRITE_TOOLS | DELETE_TOOLS | GIT_WRITE_TOOLS |
RAG_WRITE_TOOLS | CICD_WRITE_TOOLS | GITHUB_WRITE_TOOLS | GITHUB_DANGEROUS_TOOLS |
SHELL_TOOLS)` expression at lines 36-45 and bind `_WRITE_TOOLS` to the imported
frozenset. The two use sites (lines 246 and 304) need no change.

### Details

- Before: excludes `MDQ_WRITE_TOOLS`.
- After: a write-failure on an MDQ tool (`index_paths`/`refresh_index`) is
  classified fail-closed in `call()`, consistent with ADR-004.
- `X-Idempotency-Key` derivation in `call()` (lines 62-75, 209-225) is unrelated
  and unchanged.

## Compatibility considerations

`call()` is the per-request transport path; the gate now treats MDQ writes as
writes. No caller API changes.

## Security considerations

Expanding the fail-closed gate to MDQ writes is the intended ADR-004 alignment;
a transport unit test should assert the new classification before merge.

## Rollback considerations
N/A: revert the commit.

## Validation plan

| Target | Strategy | Tool / Command | Expected |
|---|---|---|---|
| `scripts/shared/http_transport.py` | Unit: MDQ write failure is fail-closed | `uv run pytest tests/mcp_servers/` transport tests | gate classifies MDQ write as fail-closed |
| Whole change | Static: mypy, ruff, import layer | `uv run mypy --no-namespace-packages scripts/`, `uv run ruff check scripts/`, `PYTHONPATH=scripts uv run lint-imports` | all pass |

## Completion criteria

- `http_transport.py` no longer defines a local `_WRITE_TOOLS` union; it uses the
  imported `ALL_SIDE_EFFECTING_TOOLS`.
- Its fail-closed write gate covers MDQ writes.
- Transport tests pass.

## Out of Scope

- Changing retry classes, `_RETRYABLE_STATUS`, or `_AMBIGUOUS_RETRY_STATUSES`.
- Editing `dispatch.py` or `tool_policy.py` (rows 02, 04).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the local `_WRITE_TOOLS` union with the imported canonical set | Completed | 20261116-071355 | 20261116-071355 |  |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261116-071355 | 20261116-071355 |  |

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
- **Requirement ID**: `REQ-003` (derive transport fail-closed write gate from the canonical set)
- **Source issue**: `issues/20261111-163800_sideeffect001_side-effect-classification-central.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261115-052032_sideeffect001_side-effect-classification-central.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261115-220459
- **Related target files**: `scripts/shared/http_transport.py`