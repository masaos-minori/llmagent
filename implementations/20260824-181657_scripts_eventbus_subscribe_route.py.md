## Goal

Add an em-dash-delimited `# nosec B608 — <justification>` annotation to the bandit
B608 false positive in `scripts/eventbus/subscribe_route.py:51`, so bandit no longer
flags this line. No change to SQL logic.

## Scope

- In scope: `scripts/eventbus/subscribe_route.py:51` (the `_fetch_replay()` inner
  function's `db.execute(f"SELECT ... IN ({placeholders}) ORDER BY seq", (start_seq,
  *topic))` call).
- Out of scope: any change to SQL query construction or parameter binding; the other 4
  target files in the same plan.

## Assumptions

- The em-dash character (U+2014, `—`) is mandatory for
  `tools/check_suppression_justification.py` — same basis as the sibling `db.py`
  procedure document.
- The value bound at `WHERE seq > ? AND topic IN ({placeholders})` uses `?`
  placeholders only; `params = (start_seq, *topic)` supplies all values positionally.
- Re-verified against current source (this cycle): line content and number still match
  the plan exactly — no drift since generation.

## Design decisions

- Append `  # nosec B608 — all values bound via ? placeholders` to the line bandit
  flags, matching the sibling annotation added to `scripts/eventbus/db.py`.
- Attach the comment to the line ending the `.execute(...)` call's SQL string
  expression (already multi-line), not by reflowing the SQL text.

## Alternatives considered

- None beyond the annotation-only approach — this is a comment addition with a single
  reasonable placement per the existing multi-line call structure.

## Implementation

### Target file

`scripts/eventbus/subscribe_route.py`

### Procedure

1. Locate the `_fetch_replay()` inner function inside the route handler.
2. Add `# nosec B608 — all values bound via ? placeholders` to the f-string SQL
   expression passed to `db.execute(...)`.
3. Confirm line length ≤ 88 chars after the edit.

### Method

Direct text edit; no code-structure change.

### Details

Current code (verified this cycle):
```python
def _fetch_replay() -> list[Any]:
    """Fetch replay events from SQLite filtered by topic and sequence."""
    if topic:
        placeholders = ",".join("?" for _ in topic)
        return list(
            db.execute(
                f"SELECT seq, event_id, topic, payload, producer, published_at"
                f" FROM events WHERE seq > ? AND topic IN ({placeholders}) ORDER BY seq",
                (start_seq, *topic),
            ).fetchall()
        )
```
Attach the nosec comment to the second f-string line (the one containing the `WHERE`
clause bandit flags).

## Compatibility considerations

Comment-only change; no runtime effect, no SQL logic change.

## Security considerations

Documents (does not change) an existing safe pattern: all query values bound via `?`
placeholders.

## Rollback considerations

Remove the added comment line; no other rollback steps required.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/eventbus/subscribe_route.py` | Static (security) | `uv run bandit -r scripts/eventbus/ -c pyproject.toml` | No B608 finding at line 51 |
| `scripts/eventbus/subscribe_route.py` | Static (suppression governance) | `uv run python tools/check_suppression_justification.py scripts/eventbus/subscribe_route.py` | No violations |
| `scripts/eventbus/subscribe_route.py` | Static (lint) | `uv run ruff check scripts/eventbus/subscribe_route.py` | No new findings |
| `tests/eventbus/` | Regression | `uv run pytest tests/eventbus/ -v` | No new failures (comment-only change) |

## Out of scope

SQL query construction/parameter binding changes; the other 4 target files in this plan.

## Execution Status

### Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: comment-only change, no new tests required |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: no documentation update in scope |

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
- **Source issue**: N/A: not applicable in this phase (the source plan's own Traceability records `Source issue: N/A` and `Source requirement: requires/20260726-121521_require.md` — this plan predates the issue-to-plan pipeline merge)
- **Source requirement**: `requires/20260726-121521_require.md`
- **Source plan**: `plans/20260823-193604_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260824-181657
- **Related target files**: `scripts/eventbus/subscribe_route.py`

## Adversarial verification notes (this cycle)

Re-verified line 51's content against current source — unchanged since the plan was
generated. Confirmed via `grep -rl "20260823-193604_plan" implementations/
implementations/done/` that no existing implementation procedure document already
covers this plan/target pair. No blocking unknowns or contradictions found.
