## Goal

Define `ALL_SIDE_EFFECTING_TOOLS` (new) in `scripts/shared/tool_constants.py` as the single canonical frozenset of side-effecting tools, and remove the contradictory routing-authority comment block so the module header is the sole authority statement. Owns the companion parity test that keeps `TOOL_LIST` `is_write=True` metadata equal to this set.

## Scope
**Release unit**: N/A: not part of a release unit

- Covers `REQ-001` (canonical frozenset) and `REQ-006` (remove contradictory comment) for the target file.
- Companion: owns `REQ-005` (exact-equality parity test) in `tests/mcp_servers/test_tool_schema_contract.py`.

## Assumptions
- Canonical membership = `WRITE_TOOLS | DELETE_TOOLS | GIT_WRITE_TOOLS | RAG_WRITE_TOOLS | CICD_WRITE_TOOLS | GITHUB_WRITE_TOOLS | GITHUB_DANGEROUS_TOOLS | SHELL_TOOLS | MDQ_WRITE_TOOLS` (verified 25 members).
- The set already equals the union of every `TOOL_LIST` entry with `is_write=True` (verified: symmetric difference empty, 25 = 25), so the parity test needs no approved exceptions today.
- `scripts/mcp_servers/server.py` already reads `ALL_SIDE_EFFECTING_TOOLS` via a `getattr(..., "ALL_SIDE_EFFECTING_TOOLS", None)` fallback with an inert-boundary guard; defining it here activates that boundary without editing `server.py` (owned by `mcproute001`).

## Design decisions
- Introduce one frozenset as the single source for dedup/retry-suppression classification; keep `is_write`, retry class, approval tier, and `WRITE_DANGEROUS` as separate dimensions (not unified).
- Leave the existing per-category sets and `get_all_mcp_tool_names()` unchanged; `ALL_SIDE_EFFECTING_TOOLS` is additive.

## Alternatives considered
- N/A: no alternative; the Plan's Design section fixes the union-composition approach and the "existing test file" parity-test location.

## Implementation
### Target file
- `scripts/shared/tool_constants.py`

### Procedure
1. After `RETRYABLE_TOOLS` (line 187-218) and before `get_all_mcp_tool_names()` (line 221), define `ALL_SIDE_EFFECTING_TOOLS` (new) as the union of the nine category sets listed above. Add a module-level docstring/comment stating it is the single classification source for dispatch dedup and HTTP fail-closed gating, and pointing to the module header (lines 4-21) as the sole routing-authority statement.
2. Delete the contradictory routing-authority comment block at lines 122-126 ("Seed data only; shared.tool_registry.ToolRegistry is the canonical/fallback routing source ..."). Keep the adjacent, non-contradictory web-search note at lines 127-129.

### Method
- Add one frozenset constant; no runtime logic changes in this file. Membership must reproduce `tool_policy._STATIC_SIDE_EFFECT_TOOLS` (verified equal, 25 members) so consumer delegation in sibling procedures is behavior-preserving.

### Details
- The union intentionally differs from `RETRYABLE_TOOLS` (line 187): `RETRYABLE_TOOLS` is a retry-class dimension (18 members, excludes `shell_run`, `trigger_workflow`, and some GitHub tools); `ALL_SIDE_EFFECTING_TOOLS` is the side-effect and dedup dimension (25 members). Do not conflate them.
- `MDQ_WRITE_TOOLS` (`index_paths`, `refresh_index`; line 94) must be included — they route through `dispatch_tool()` and are the tools the current dispatch/http unions wrongly omit.

### Companion test files
- `tests/mcp_servers/test_tool_schema_contract.py`
  - Procedure: add `test_side_effect_parity_matches_canonical` (new) that imports `ALL_SIDE_EFFECTING_TOOLS` and reuses `_TOOL_LIST_MODULES` (lines 24-38) to collect every `TOOL_LIST` entry with `is_write=True`, then asserts exact equality against the canonical set; keep an explicit, currently-empty `APPROVED_EXCEPTIONS` frozenset so any future drift fails in CI rather than being silently allowed.
  - Validation: `pytest tests/mcp_servers/test_tool_schema_contract.py` — the new assertion passes with an empty symmetric difference; existing `test_tool_name_coverage_matches_tool_constants` (line 51) and the schema-v2 contract test stay green.

## Compatibility considerations
- Additive constant + comment removal only; no existing symbol removed, so no caller breaks. `server.py`'s `getattr` fallback begins returning the real set once defined (no `server.py` edit here).
- `import` layer contract preserved: `ALL_SIDE_EFFECTING_TOOLS` lives in `shared/` and consumers under `scripts/` import it.

## Security considerations
- Centralizing side-effect membership closes the silent-omission risk (ADR-004 fail-closed-on-writes): a new write tool omitted from a consumer union can no longer slip past dedup/retry suppression, because consumers will import this single set.

## Rollback considerations
- Revert the commit: remove the new constant and restore the removed comment block. No data or persistence change.

## Validation plan
- `pytest tests/mcp_servers/test_tool_schema_contract.py` — parity assertion passes (canonical == `is_write=True` set, empty symmetric difference).
- `PYTHONPATH=scripts uv run lint-imports` — `shared.tool_constants` remains importable by `dispatch`, `http_transport`, `tool_policy`.
- `uv run ruff check scripts/shared/tool_constants.py` and `uv run mypy --no-namespace-packages scripts/` — clean.

## Completion criteria
- `ALL_SIDE_EFFECTING_TOOLS` exists in `scripts/shared/tool_constants.py` with exactly the 25 verified members (MDQ included).
- The contradictory comment (lines 122-126) is gone; the module header (lines 4-21) is the only routing-authority statement.
- Companion parity test exists and passes with an empty approved-exception set.

## Out of Scope
- Editing `scripts/mcp_servers/server.py`'s idempotency boundary (`mcproute001` owns it); changing `is_write`, retry classes, approval tiers, or `WRITE_DANGEROUS`; any `docs/*.md` change (no documentation row in this Plan's `Implementation Target Files`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Define `ALL_SIDE_EFFECTING_TOOLS` union with authority-pointing docstring | Pending | — | — | REQ-001 |
| 2 | Delete contradictory routing-authority comment block (lines 122-126) | Pending | — | — | REQ-006; keep lines 127-129 |
| 3 | Add companion parity test `test_side_effect_parity_matches_canonical` | Pending | — | — | REQ-005; companion test file |
| 4 | Run validation sequence (`rules/toolchain.md`) | Pending | — | — | pytest parity + lint-imports + ruff/mypy |

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
- **Requirement ID**: `REQ-001` (canonical side-effect set), `REQ-006` (remove contradictory comment); companion `REQ-005` (parity test)
- **Source issue**: `issues/20261111-163800_sideeffect001_side-effect-classification-central.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261115-052032_sideeffect001_side-effect-classification-central.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261115-192353
- **Related target files**: `scripts/shared/tool_constants.py`, `tests/mcp_servers/test_tool_schema_contract.py`
