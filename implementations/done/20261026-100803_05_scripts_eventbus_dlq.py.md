## Goal

Classify the `REQ-0xx` tag comments in `dlq.py` as active-invariant (kept) versus
resolved-history (removed/rewrite). Adversarial verification found all four tags are active
invariants; no edit is required.

## Scope

- Inspect only `scripts/eventbus/dlq.py`'s `REQ-0xx` tags. No modification is required.

## Assumptions

- The classification test is: does the comment state a CURRENT invariant/failure/concurrency
  rule (keep) or narrate a PAST removed implementation such as "removed"/"replaced by"/
  "legacy"/"no longer written" (remove/rewrite)?
- Comment edits would not change observable behavior; here none are needed.

## Design decisions

- **Keep all four `REQ-0xx` tags.** Each states a current invariant:
  - Line 32: `# REQ-002: per-consumer failure count`.
  - Line 84: `REQ-002 and ADR-006 INV-13: promotes events where every consumer with a delivery`.
  - Line 132: `Per-consumer failure count (REQ-002).`
  - Line 189: `Per-consumer failure count (REQ-002).`
- None narrates resolved history, so no removal or rewrite is performed.

## Alternatives considered

- None; all tags are current-state markers.

## Implementation

### Target file

`scripts/eventbus/dlq.py`

### Procedure

1. Confirm each of the four `REQ-0xx` tags (lines 32, 84, 132, 189) states a current
   invariant (see Design decisions).
2. No edit is required.

### Method

Read-only classification sweep; no edits.

### Details

- Verification: `grep -rn "REQ-0" scripts/eventbus/dlq.py` returns 4 tags; none contains a
  past-tense "removed"/"replaced by"/"legacy"/"no longer" phrase.

## Compatibility considerations

- No change; behavior unchanged.

## Security considerations

- No security impact; no change.

## Rollback considerations

- N/A: no change.

## Validation plan

- `uv run pytest tests/eventbus/` — full EventBus suite passes (unchanged).
- `uv run ruff check scripts/eventbus/dlq.py`; `uv run mypy scripts/eventbus/dlq.py`;
  `uv run bandit scripts/eventbus/ -c pyproject.toml`.
- `PYTHONPATH=scripts uv run lint-imports` — `eventbus-is-isolated` KEPT.

## Completion criteria

- All four `REQ-0xx` tags confirmed active invariants; no resolved-history narrative remains.

## Out of Scope

- Any modification to `dlq.py` beyond this classification confirmation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Classify REQ-0xx tags; keep active invariants | Pending | — | — | all 4 tags active; no edit required |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: no change |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A |

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
- **Requirement ID**: `REQ-001`
- **Source issue**: `issues/20261023-154326_eventbus008_documentation-comment-drift-cleanup.md`
- **Requirement requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-124800_eventbus008_documentation-comment-drift-cleanup.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261026-100803
- **Related target files**: `scripts/eventbus/dlq.py`
