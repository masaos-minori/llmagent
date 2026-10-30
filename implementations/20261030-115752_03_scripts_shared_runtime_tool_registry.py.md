# Implementation Procedure: `scripts/shared/runtime_tool_registry.py`

## Goal

Remove the fail-open `allowed_servers=None` default: the Security Posture gate becomes a required constructor input, `None` raises `TypeError`, an explicit empty set denies all (REQ-001: required explicit allowlist, deny-all empty set).

## Scope

- `scripts/shared/runtime_tool_registry.py` `__init__` and `_exclusion_reason` only.
- The sole production caller `scripts/agent/services/mcp_tool_discovery_registry.py:92` already passes `allowed_servers` (verified `return RuntimeToolRegistry(tools=built, allowed_servers=allowed_servers)`); no other `scripts/` construction exists.

## Assumptions

- The 45 test constructions (12 files) migrate in their own target rows (rows 11-22); this row does not edit tests. Expect `tests/` to go red between this row and the migration rows — land them inside the same Phase 2 batch (plan Phase 2 migrates per file with the affected test run after each step).
- `tools`, `unavailable_servers`, `server_configs` keep their defaults; only `allowed_servers` loses one (plan Scope lists only the allowlist change).

## Design decisions

- Signature: `allowed_servers: frozenset[str]` with no default, positioned last as today (:49) — every caller must name it explicitly; keyword calls keep working.
- Runtime `None` guard raises `TypeError` with a message naming the removal of allow-all semantics: the static type annotation cannot stop `None` from arriving dynamically (plan AC-1 requires the `TypeError`).
- `_exclusion_reason` (:91-95): drop the `self._allowed_servers is not None` precondition so the posture filter applies unconditionally; the `"posture"` exclusion reason and `_posture_excluded` reporting stay byte-identical in behavior (REQ-008 observable reason preserved).

## Alternatives considered

- Keep the parameter optional but raise on omission via a sentinel — rejected: REQ-001 says required input; a sentinel re-introduces a no-gate code path reviewers must audit.
- Remove the parameter and derive the allowlist internally — rejected: `shared` is a leaf and cannot read posture DTOs (REQ-007; existing docstring at :53-56 states this constraint).

## Implementation

### Target file

`scripts/shared/runtime_tool_registry.py`

### Procedure

1. `__init__` (:45-67): change `allowed_servers: frozenset[str] | None = None` to `allowed_servers: frozenset[str]`; add at the top of the body `if allowed_servers is None: raise TypeError(...)` naming that the Security Posture gate is mandatory and an explicit `frozenset()` means deny-all.
2. Rewrite the `__init__` docstring paragraph (:53-56): `None` is no longer accepted; the set is authoritative; empty registers nothing.
3. `_exclusion_reason` (:91-95): replace the two-part condition `self._allowed_servers is not None and server_key not in self._allowed_servers` with `server_key not in self._allowed_servers`.
4. Update the module-level docstring (:17) describing the gate so no prose still offers a no-gate mode.

### Method

Single-file mechanical refactor; behavior for every existing non-`None` call is unchanged (the filter previously ran whenever a set was supplied — it now always runs).

### Details

- The empty-set deny-all path already works today (`_exclusion_reason` excludes every key absent from an empty set; existing test `tests/shared/test_runtime_tool_registry.py:518` pins it) — this row only makes it the sole path.
- Keep the posture-exclusion warning log (`logger.warning` on `self._posture_excluded`, :66-69) unchanged.
- AC-1 grep gate applies after the migration rows: no `allowed_servers=None` remains in `scripts/` or `tests/`; this row removes the only `scripts/` occurrence (the signature itself).

## Compatibility considerations

- All 45 test constructions must migrate (rows 11-22); run `uv run pytest tests/shared tests/agent` per file after each migration step (plan Phase 2).
- No serialization/persistence of the constructor exists; no external API surface beyond the repo.

## Security considerations

- This is the fail-closed change itself: absence of the gate becomes a programming error (TypeError), never an allow-all behavior (plan Problem 1).

## Rollback considerations

- Reverting this row alone re-opens the `None` default; rollback must also revert rows 11-22 to keep tests consistent — revert as one Phase 2 commit.

## Validation plan

- `uv run pytest tests/shared tests/agent`, `uv run pytest tests/integration/test_production_security_regression.py` (after the migration rows land).
- Gates: `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `uv run mypy scripts`, `uv run ruff check scripts tests tools`, `uv run bandit -r scripts`, `PYTHONPATH=scripts uv run lint-imports`.
- `rg 'allowed_servers=None' scripts/ tests/` finds nothing (plan AC-1).

## Completion criteria

- Constructing `RuntimeToolRegistry({...})` without `allowed_servers` raises `TypeError`; passing `None` raises `TypeError`; an empty allowlist registers nothing and reports a posture exclusion; production startup is unchanged for the current all-required configuration (plan AC-1, AC-6).

## Out of Scope

- The 12 test-file migrations (rows 11-22); `mcp_tool_discovery*.py` (already required inputs, plan Excluded); mandatoriness registry wiring (rows 1-5).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Refactor `__init__` + `_exclusion_reason` + docstrings per Procedure | Pending | — | — | |
| 2 | Characterization: existing deny-all/posture tests (`tests/shared/test_runtime_tool_registry.py` :499-597) stay green after row 11's migration | Pending | — | — | Row 11 also adds the `None`-rejection regression |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | N/A: no docs in this row (row 25 covers ADR text) | — | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 3 | Full-suite green requires rows 11-22 migrated in the same batch | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

#### Marker edit record
- `(new)` マーカー編集（この doc が導入する新規コンポーネント）は `tools/mark_new_115752.py`（冪等）に記録済み。

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001 (required explicit `allowed_servers`; `None` raises `TypeError`; empty set denies all)
- **Source issue**: `issues/20261029-104502_mcpgate001_mcp-mandatory-construction-contracts.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261030-001153_mcpgate001_mcp-mandatory-construction-contracts.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-115752
- **Related target files**: `scripts/shared/runtime_tool_registry.py`
