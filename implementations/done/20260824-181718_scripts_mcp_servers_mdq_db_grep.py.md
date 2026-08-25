## Goal

Add an em-dash-delimited `# nosec B608 — <justification>` annotation to the bandit
B608 false positive in `scripts/mcp_servers/mdq/db_grep.py:70`, so bandit no longer
flags this line. No change to SQL logic.

## Scope

- In scope: `scripts/mcp_servers/mdq/db_grep.py:70` (the `_fetch_chunk_rows()`
  function's `conn.execute(f"SELECT ... FROM chunks {where_clause}", params)` call).
- Out of scope: any change to `where_clause` construction or parameter binding; the
  other 4 target files in the same plan; `scripts/mcp_servers/mdq/search.py` (already
  correctly annotated, confirmed out of scope by the plan).

## Assumptions

- The em-dash character (U+2014, `—`) is mandatory for
  `tools/check_suppression_justification.py` — same basis as the sibling procedure
  documents in this batch.
- `where_clause` is built from fixed column-name fragments by the caller (not raw user
  input), and `params` supplies all bound values — matches the plan's justification
  text ("WHERE clause built from fixed column names; values bound via params").
- Re-verified against current source (this cycle): line content and number still match
  the plan exactly — no drift since generation.

## Design decisions

- Append `  # nosec B608 — WHERE clause built from fixed column names; values bound
  via params` to the line bandit flags.

## Alternatives considered

- None beyond the annotation-only approach.

## Implementation

### Target file

`scripts/mcp_servers/mdq/db_grep.py`

### Procedure

1. Locate `_fetch_chunk_rows()`.
2. Add the nosec annotation to the `f"SELECT ... {where_clause}"` line passed to
   `conn.execute(...)`.
3. Confirm line length ≤ 88 chars after the edit; if it would exceed 88, wrap using the
   same multi-line style already used at sibling call sites in this file/module.

### Method

Direct text edit; no code-structure change.

### Details

Current code (verified this cycle):
```python
def _fetch_chunk_rows(
    conn: sqlite3.Connection, where_clause: str, params: list
) -> list[sqlite3.Row]:
    """Fetch chunk rows eligible for grep matching, filtered by `where_clause`."""
    return conn.execute(
        f"SELECT chunk_id, source_path, heading_path, heading, content, start_line FROM chunks {where_clause}",
        params,
    ).fetchall()
```
This line already exceeds 88 chars pre-existing (long column list); attach the nosec
comment to the closing `params,` line or reflow only the comment placement, not the SQL
text itself, to avoid compounding the pre-existing length issue.

## Compatibility considerations

Comment-only change; no runtime effect, no SQL logic change.

## Security considerations

Documents (does not change) an existing safe pattern: `where_clause` is built from
fixed column-name fragments, not raw user input; values are bound via `params`.

## Rollback considerations

Remove the added comment line; no other rollback steps required.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/mcp_servers/mdq/db_grep.py` | Static (security) | `uv run bandit -r scripts/mcp_servers/mdq/ -c pyproject.toml` | No B608 finding at line 70 |
| `scripts/mcp_servers/mdq/db_grep.py` | Static (suppression governance) | `uv run python tools/check_suppression_justification.py scripts/mcp_servers/mdq/db_grep.py` | No violations |
| `scripts/mcp_servers/mdq/db_grep.py` | Static (lint) | `uv run ruff check scripts/mcp_servers/mdq/db_grep.py` | No new findings |
| mdq test suite | Regression | `uv run pytest tests/mcp_servers/mdq/ -v` | No new failures (comment-only change) |

## Out of scope

`where_clause`/parameter-binding logic changes; `search.py`; the other 4 target files
in this plan; the pre-existing line-length issue (not introduced by this change).

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
- **Generated at**: 20260824-181718
- **Related target files**: `scripts/mcp_servers/mdq/db_grep.py`

## Adversarial verification notes (this cycle)

Re-verified line 70's content against current source — unchanged since the plan was
generated. Confirmed via `grep -rl "20260823-193604_plan" implementations/
implementations/done/` that no existing implementation procedure document already
covers this plan/target pair. No blocking unknowns or contradictions found.
