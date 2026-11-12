## Goal
Correct `DLQ events are written as JSONL files` in `eventbus_01` to the per-event JSON artifact statement (`REQ-001` / `AC-1`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Line numbers have drifted from the Plan; locate each passage by its quoted text, and skip and report it if it is already correct (Phase 1 rule).
- Confirmed: `scripts/eventbus/dlq.py` writes `{deadletter_dir}/{event_id}.json`; the `events.jsonl` archive is a separate secondary store (checked).

## Design decisions
- One sentence changed; the SQLite-primary statement stays.

## Alternatives considered
N/A: the Plan fixes the approach for this row.

## Implementation
### Target file
`docs/24_eventbus/eventbus_01_system-overview.md`

### Procedure
1. Replace the Persistence bullet's DLQ clause.

### Method
- New text: `All events are stored in SQLite, and each DLQ event is also written as a per-event JSON file (`{event_id}.json`) in the dead-letter directory.`

### Details
- Do not add configuration key names; link wording stays as is.

## Compatibility considerations
N/A: documentation-only change; no code, config, or schema impact.

## Security considerations
N/A: no authorization, secret, or trust-boundary change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_consistency.py --domain eventbus` — pass.
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_japanese.py` — pass.
- `uv run python tools/check_needs_confirmation_inventory.py` — pass.

## Completion criteria
- The Persistence bullet names per-event JSON files; the eventbus consistency check passes.

## Out of Scope
- `events.jsonl` retention text (row 10).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261112-204830 | 20261112-204830 |  |
| 2 | Run the documentation checkers per Validation plan | Completed | 20261112-204830 | 20261112-204830 |  |

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
- **Requirement ID**: `REQ-001` — DLQ artifacts are per-event JSON files
- **Source issue**: issues/20261109-113421_adrrev019_docs-stale-statements.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-112439_adrrev019_docs-stale-statements.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-124641
- **Related target files**: `docs/24_eventbus/eventbus_01_system-overview.md`