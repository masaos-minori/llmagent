## Goal

Classify the `REQ-0xx` tag comments in `subscribe_route.py` as active-invariant (kept)
versus resolved-history (removed/rewrite). Adversarial verification found all sixteen tags are
active invariants; no edit is required.

## Scope

- Inspect only `scripts/eventbus/subscribe_route.py`'s `REQ-0xx` tags. No modification is
  required.

## Assumptions

- The classification test is: does the comment state a CURRENT invariant/failure/concurrency
  rule (keep) or narrate a PAST removed implementation such as "removed"/"replaced by"/
  "legacy"/"no longer written" (remove/rewrite)?
- Comment edits would not change observable behavior; here none are needed.

## Design decisions

- **Keep all sixteen `REQ-0xx` tags.** Each states a current invariant:
  - Lines 64, 78, 82: principal ownership / fail-closed identity / topic-access validation.
  - Lines 98, 107, 122, 136: Last-Event-ID / resume-position precedence / stale-reconnect rules.
  - Lines 190, 258: emit `id:` alongside `data:`.
  - Lines 205, 209, 231, 236, 241: heartbeat tracking, timeout disconnect, deadline eval,
    heartbeat-if-deadline, idle-timeout reset.
  - Lines 260, 262: update last-event time; periodic heartbeat during active delivery.
- None narrates resolved history, so no removal or rewrite is performed.

## Alternatives considered

- None; all tags are current-state markers.

## Implementation

### Target file

`scripts/eventbus/subscribe_route.py`

### Procedure

1. Confirm each of the sixteen `REQ-0xx` tags (lines 64, 78, 82, 98, 107, 122, 136, 190,
   205, 209, 231, 236, 241, 258, 260, 262) states a current invariant (see Design decisions).
2. No edit is required.

### Method

Read-only classification sweep; no edits.

### Details

- Verification: `grep -rn "REQ-0" scripts/eventbus/subscribe_route.py` returns 16 tags; none
  contains a past-tense "removed"/"replaced by"/"legacy"/"no longer" phrase.

## Compatibility considerations

- No change; behavior unchanged.

## Security considerations

- No security impact; no change.

## Rollback considerations

- N/A: no change.

## Validation plan

- `uv run pytest tests/eventbus/` — full EventBus suite passes (unchanged).
- `uv run ruff check scripts/eventbus/subscribe_route.py`; `uv run mypy
  scripts/eventbus/subscribe_route.py`; `uv run bandit scripts/eventbus/ -c pyproject.toml`.
- `PYTHONPATH=scripts uv run lint-imports` — `eventbus-is-isolated` KEPT.

## Completion criteria

- All sixteen `REQ-0xx` tags confirmed active invariants; no resolved-history narrative
  remains.

## Out of Scope

- Any modification to `subscribe_route.py` beyond this classification confirmation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Classify REQ-0xx tags; keep active invariants | Pending | — | — | all 16 tags active; no edit required |
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
- **Related target files**: `scripts/eventbus/subscribe_route.py`
