## Goal

Rewrite the legacy-counter narrative comment in `delivery_repo.py` to the current
per-consumer invariant; classify the remaining `REQ-0xx` tags (all active invariant markers,
kept).

## Scope

- Modify only `scripts/eventbus/delivery_repo.py`: the legacy-counter comment at lines
  110-112. All `REQ-0xx` tags here are active invariants and are kept unchanged.

## Assumptions

- The comment at lines 110-112 narrates past history ("legacy and no longer written"); it is
  rewritten to state the current invariant.
- The four `REQ-0xx` tags (lines 41, 179, 188, 204) each state a current
  idempotency/existence/DLQ/ack invariant and are kept. (The Plan's row listed lines
  41/179/188; line 204 is a fourth active `REQ-005` marker, also kept.)
- Comment edits do not change observable behavior; the ACK/NACK suite is the backstop.

## Design decisions

- **Rewrite** lines 110-112 from
  ```
  # Per-consumer model: only the per-consumer counter is authoritative for
  # DLQ promotion; the events-level failure counters are legacy and no longer
  # written to under the per-consumer model.
  ```
  to a present-tense invariant that drops "legacy"/"no longer", e.g.
  ```
  # Per-consumer model: only the per-consumer failure counter is authoritative for
  # DLQ promotion (ADR-006 INV-13); there is no events-level failure counter under
  # this model.
  ```
- **Keep** all four `REQ-0xx` tags (lines 41, 179, 188, 204).

## Alternatives considered

- Deleting the comment entirely: rejected; the per-consumer-authoritative-counter invariant
  is a current concurrency/durability rule worth stating.

## Implementation

### Target file

`scripts/eventbus/delivery_repo.py`

### Procedure

1. Replace the three-line comment at lines 110-112 with the present-tense invariant above
   (drop "legacy"/"no longer written").
2. Leave all four `REQ-0xx` tags (lines 41, 179, 188, 204) untouched.

### Method

One comment rewrite in one file; no new symbols.

### Details

- Do not alter any code path, return value, or delivery logic.
- Verification: `grep -rn "REQ-0" scripts/eventbus/delivery_repo.py` returns 4 tags; none
  should contain a past-tense "removed"/"legacy"/"no longer" phrase.

## Compatibility considerations

- Behavior unchanged; only comment text changed.

## Security considerations

- No security impact; comment-only edit.

## Rollback considerations

- Revert the commit.

## Validation plan

- `uv run pytest tests/eventbus/` — full EventBus suite passes.
- `uv run ruff format scripts/eventbus/delivery_repo.py`; `uv run ruff check
  scripts/eventbus/delivery_repo.py`; `uv run mypy scripts/eventbus/delivery_repo.py`;
  `uv run bandit scripts/eventbus/ -c pyproject.toml`.
- `PYTHONPATH=scripts uv run lint-imports` — `eventbus-is-isolated` KEPT.

## Completion criteria

- The legacy-counter comment states the current per-consumer invariant without
  "legacy"/"no longer"; four `REQ-0xx` tags remain, all active invariants.

## Out of Scope

- Any change outside `delivery_repo.py`.
- Editing the four active `REQ-0xx` tags.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite legacy-counter comment (lines 110-112) | Pending | — | — | drop "legacy"/"no longer" |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: comment-only |
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
- **Related target files**: `scripts/eventbus/delivery_repo.py`
