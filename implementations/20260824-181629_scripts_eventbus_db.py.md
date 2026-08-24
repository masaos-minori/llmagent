## Goal

Add an em-dash-delimited `# nosec B608 — <justification>` annotation to the bandit
B608 false positive in `scripts/eventbus/db.py:210`, so bandit no longer flags this
line. No change to SQL logic.

## Scope

- In scope: `scripts/eventbus/db.py:210` (the `f"SELECT seq, event_id, topic, payload,
  producer, published_at" f" FROM events WHERE seq > ? AND topic IN ({placeholders})
  ORDER BY seq"` expression, and its `else` branch on the following line).
- Out of scope: any change to SQL query construction, parameter binding, or logic;
  the other 4 target files in the same plan (each has its own implementation procedure
  document); `scripts/eventbus/db.py:23`'s existing `busy_timeout` nosec annotation
  (different, already-annotated finding).

## Assumptions

- The em-dash character (U+2014, `—`) is mandatory for
  `tools/check_suppression_justification.py` to accept the annotation — confirmed by
  reading the tool's `EM_DASH = "—"` constant and by the existing
  `scripts/eventbus/db.py:23` / `scripts/db/maintenance.py:169` /
  `scripts/mcp_servers/mdq/search.py:152,167` annotations, all of which use `—`, not `-`.
- The value bound via `?` at line 210's `WHERE seq > ?` (and the `IN ({placeholders})`
  clause, itself built from `?` placeholders joined by `,`, not raw values) — confirmed
  by reading `params = (since_seq,) + tuple(topics)` on the following line.
- Re-verified against current source (this cycle): the line content and line number
  still match the plan exactly — no drift since the plan was generated.

## Design decisions

- Append `  # nosec B608 — all values bound via ? placeholders` (two spaces before `#`,
  matching the existing `db.py:23` style) to the line bandit flags.
- Verify the resulting line still fits within 88 chars per `rules/coding.md`; if not,
  attach the comment to the closing paren/line of the existing multi-line f-string
  instead of reflowing the SQL text itself.

## Alternatives considered

- Restructuring the query to use a parameterized `IN` clause helper to silence bandit
  structurally — rejected: out of scope per the plan (annotation-only change; no SQL
  logic change), and the existing pattern (`?` placeholders joined by `,`) is already
  correct and used elsewhere in the codebase (e.g. `subscribe_route.py`).

## Implementation

### Target file

`scripts/eventbus/db.py`

### Procedure

1. Locate the function containing line 210 (returns events with `seq > since_seq`,
   optionally filtered by topics).
2. Add `# nosec B608 — all values bound via ? placeholders` to the `if topics:` branch's
   SQL construction (the `f"..."` expression assigned to `sql`).
3. Confirm line length ≤ 88 chars after the edit; if not, attach the comment to the
   closing line of the existing multi-line f-string rather than reflowing.

### Method

Direct text edit; no code-structure change.

### Details

Current code (verified this cycle):
```python
if topics:
    placeholders = ",".join("?" for _ in topics)
    sql = (
        f"SELECT seq, event_id, topic, payload, producer, published_at"
        f" FROM events WHERE seq > ? AND topic IN ({placeholders}) ORDER BY seq"
    )
    params = (since_seq,) + tuple(topics)
else:
    sql = "SELECT seq, event_id, topic, payload, producer, published_at FROM events WHERE seq > ? ORDER BY seq"
```
The `else` branch's line already exceeds 88 chars pre-existing (not introduced by this
change) — attach the nosec comment to the closing line of the `if topics:` branch's
parenthesized expression, not the `else` branch's already-long line, to avoid
compounding an unrelated pre-existing length issue.

## Compatibility considerations

Comment-only change; no runtime effect, no SQL logic change.

## Security considerations

This annotation documents (does not change) an existing safe pattern: all query values
are bound via `?` placeholders, never f-string-interpolated into the SQL text itself.

## Rollback considerations

Remove the added comment line; no other rollback steps required.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/eventbus/db.py` | Static (security) | `uv run bandit -r scripts/eventbus/ -c pyproject.toml` | No B608 finding at line 210 |
| `scripts/eventbus/db.py` | Static (suppression governance) | `uv run python tools/check_suppression_justification.py scripts/eventbus/db.py` | No violations |
| `scripts/eventbus/db.py` | Static (lint) | `uv run ruff check scripts/eventbus/db.py` | No new findings |
| `tests/eventbus/` | Regression | `uv run pytest tests/eventbus/ -v` | No new failures (comment-only change) |

## Out of scope

SQL query construction/parameter binding changes; the other 4 target files in this
plan; the pre-existing `else` branch line-length issue (not introduced by this change).

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
- **Generated at**: 20260824-181629
- **Related target files**: `scripts/eventbus/db.py`

## Adversarial verification notes (this cycle)

- Re-verified line 210's content and the surrounding function against current source —
  unchanged since the plan was generated; the plan's line number and justification text
  remain accurate.
- Confirmed `scripts/eventbus/db.py:23` already carries an unrelated, correctly-formatted
  nosec annotation (busy_timeout, not the target of this item) — no conflict.
- Confirmed via `grep -rl "20260823-193604_plan" implementations/ implementations/done/`
  that no existing implementation procedure document already covers this plan/target
  pair. No blocking unknowns or contradictions found.
