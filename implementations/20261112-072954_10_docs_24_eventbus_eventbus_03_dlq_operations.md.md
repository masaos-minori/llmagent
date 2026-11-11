## Goal

Replace the "metered" wording in `docs/24_eventbus/eventbus_03_dlq_operations.md` (Failure Behavior Summary, line 180) with a description of how DLQ artifact-generation failures are now observable through `/health` (`terminal_failed_outbox`, `last_dlq_sweep.result`, and the `dlq_sweep_failing` / `dlq_outbox_failed` degraded reasons), so the document states what is actually observable instead of claiming a non-existent metrics endpoint (`REQ-006` / `AC-6`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- There is no `/metrics` route (UNK-02 / Plan Background), so "metered" overstates observability.
- Outbox generation failures are recorded on the `dlq_outbox` row with exponential backoff and become terminal `failed` after `outbox_max_attempts` (existing behavior, unchanged).
- The sibling route change (`scripts/eventbus/health_route.py`, seq 03) surfaces terminal-failed outbox rows as `terminal_failed_outbox` + `dlq_outbox_failed`, and a failing `_dlq_loop` cycle as `last_dlq_sweep.result == "failed"` + `dlq_sweep_failing` (seq 02 records the result).
- Failures still "never block other events" — the outbox worker processes each due row independently.

## Design decisions
- Edit only the single cell at line 180; keep the rest of the Failure Behavior Summary table intact.
- Replace "metered" with a factual statement pointing at the `/health` fields/reasons that expose these failures, and note that they return HTTP 503 like every degraded reason.

## Alternatives considered
- Rewriting the whole Failure Behavior Summary table: rejected — only the DLQ artifact-generation row is affected by the "metered" claim; the other rows are correct.

## Implementation
### Target file
`docs/24_eventbus/eventbus_03_dlq_operations.md`

### Procedure
1. Replace the word "metered" in the line-180 cell with a description of the `/health` observability for outbox generation failures.
2. Keep the rest of that cell ("Attempt recorded on the outbox row with exponential backoff; terminal `failed` after `outbox_max_attempts`; logged, never blocks other events").
3. Do not alter other rows, sections, or documents.

### Method
Replace line 180 with:

> | DLQ artifact generation failure | Attempt recorded on the outbox row with exponential backoff; terminal `failed` after `outbox_max_attempts`; reported through `/health` (`terminal_failed_outbox` when terminal-failed rows exist, `last_dlq_sweep.result == "failed"` when the sweep cycle fails, each adding a `dlq_outbox_failed` / `dlq_sweep_failing` degraded reason that returns HTTP 503), logged, never blocks other events |

### Details
- The outbox worker (`process_outbox`) generates each artifact; a failed generation increments the attempt counter and re-queues with exponential backoff until `outbox_max_attempts`, then the outbox row's `status` becomes `failed` (terminal). This is unchanged.
- `/health` reports the count of terminal-failed rows (`terminal_failed_outbox`) and the last sweep cycle's result (`last_dlq_sweep.result`); both are documented in `eventbus_10` (seq 09).
- No `/metrics` route exists, so the document no longer claims a metric; it points at the actual `/health` surface instead.

## Compatibility considerations
- Documentation-only. No other Plan targets `eventbus_03`; `check_docs_consistency.py --domain eventbus` must pass.

## Security considerations
- None: operational documentation only.

## Rollback considerations
- N/A: revert the commit; the edit is localized to this document.

## Validation plan
- `uv run python tools/check_docs_consistency.py --domain eventbus` — pass.
- `uv run python tools/check_docs_content_policy.py --strict`, `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_japanese.py` — pass.

## Completion criteria
- `eventbus_03` no longer says "metered"; it describes the `/health` fields and degraded reasons that expose outbox generation failures.
- `check_docs_consistency.py --domain eventbus` passes.

## Out of Scope
- Adding a `/metrics` route — out of scope (UNK-02).
- The route change that produces the `/health` fields — sibling procedure (`scripts/eventbus/health_route.py`, seq 03).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: `REQ-006` — replace the "metered" wording with the observable `/health` fields and degraded reasons
- **Source issue**: issues/20261109-113152_adrrev014_eventbus-spec-gaps.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-103238_adrrev014_eventbus-spec-gaps.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-072954
- **Related target files**: `docs/24_eventbus/eventbus_03_dlq_operations.md`
