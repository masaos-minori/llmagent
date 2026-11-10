## Goal
- Remove the eventbus domain from the recovery drill (REQ-004).

## Scope
**Release unit**: db-eventbus-removal

- In scope: this one file, Phase 3 of the Plan.
- Not in scope: any other file; a second file needed here is an additional-target discovery.
- Execution order follows the Plan's phases, not `seq`: Phase 1 (documents 03, 04), Phase 2 (05, 18), Phase 3 (the `scripts/db`, `scripts/shared`, validator, config, and test documents, one release unit), Phase 4 (01, 38, 39), Phase 5 (the document rows), Phase 6 verification.

## Assumptions
- Overlap with plans 003, 004, 005, 006 (judged in the Plan's Assumptions): sequencing or different keys; no contradiction on this file.
- The Plan's Step 3a corrections apply (EventBus tool reads `db_path` with its own reader; `eventbus_schema_version` and the DDL text accessor move to `scripts/eventbus/db_tools.py`).

## Design decisions
- Remove only what the Plan names for this file; keep every other behavior unchanged.

## Alternatives considered
N/A: the ownership decision (EventBus-side tooling, maintainer 2026-11-10) is fixed in the Plan's Design section.

## Implementation
### Target file
`scripts/db/recovery_drill.py`

### Procedure
1. Remove `"eventbus"` from `DOMAINS` (`recovery_drill.py:47`), delete `_verify_eventbus` (`:125-139`), the `"eventbus": cfg.eventbus_db_path` entry (`:157`), the `else` branch that calls it (`:211`), and the `shared.eventbus_schema_fingerprint` import (`:29`); update the module docstring (lines 1-6) and the CLI choices (`:311`).
2. Keep the drill for rag, session, workflow, including its audit artifact shape.

### Method
- Targeted edits; remove imports left unused as `ruff` reports them.

### Details
- The EventBus-side `verify` (document 03) covers the integrity and fingerprint checks `_verify_eventbus` made; the RPO/RTO artifact for eventbus is dropped (Plan UNK-03).

### Companion test files
- `tests/db/test_recovery_drill.py`
  - Procedure: Remove the eventbus fixtures (`:28, 277`), the `eventbus_db_path=` config lines (`:286, 304`), and expectations for four domains.
  - Validation: `uv run pytest tests/db/test_recovery_drill.py -v`

## Compatibility considerations
- See Details; the removal is intentional and has no shim (`tools/check_compat_shims.py`).

## Security considerations
- No authentication or authorization behavior changes; the EventBus path and schema checks stay fail-closed.

## Rollback considerations
- Revert the phase's commit; Phases 1-2 keep the Agent-side path available until Phase 3 lands, so a revert of Phase 3 restores the old behavior.

## Validation plan
- `uv run pytest tests/db/test_recovery_drill.py -v`.
- `uv run ruff check scripts/ tests/ tools/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`.

## Completion criteria
- The drill covers three domains; no eventbus reference remains in the module.

## Out of Scope
- Editing any other file.
- Redesigning the EventBus, its schema, or its authorization.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change in `scripts/db/recovery_drill.py` | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
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
- **Requirement ID**: REQ-004
- **Source issue**: issues/20261109-112538_adrrev002_agent-eventbus-coupling.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-091327_adrrev002_agent-eventbus-coupling.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-102050
- **Related target files**: `scripts/db/recovery_drill.py`, `tests/db/test_recovery_drill.py`
