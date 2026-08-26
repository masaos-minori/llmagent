## Goal

Add an em-dash-delimited `# nosec B608 — <justification>` annotation to the bandit
B608 false positive in `scripts/mcp_servers/mdq/health_check.py:35`, so bandit no
longer flags this line. No change to SQL logic.

## Scope

- In scope: `scripts/mcp_servers/mdq/health_check.py:35` (the
  `_check_stale_documents()` function's `conn.execute(f"SELECT COUNT(*) as cnt FROM
  documents WHERE {STALE_SQL_CONDITION}")` call).
- Out of scope: any change to `STALE_SQL_CONDITION` or query logic; the other 4 target
  files in the same plan.

## Assumptions

- `STALE_SQL_CONDITION` (`scripts/mcp_servers/mdq/mdq_models.py:313`) is a fixed
  module-level string constant (`"mtime_ns > CAST(indexed_at * 1e9 AS INTEGER)"`),
  imported via `from mcp_servers.mdq.mdq_models import STALE_SQL_CONDITION` — confirmed
  via `grep -rn "STALE_SQL_CONDITION" scripts/mcp_servers/mdq/`. No user input reaches
  this f-string.
- The em-dash character (U+2014, `—`) is mandatory for
  `tools/check_suppression_justification.py` — same basis as the sibling procedure
  documents in this batch.
- Re-verified against current source (this cycle): line content and number still match
  the plan exactly — no drift since generation.

## Design decisions

- Append `  # nosec B608 — STALE_SQL_CONDITION is a fixed string constant` to the line
  bandit flags.

## Alternatives considered

- None beyond the annotation-only approach.

## Implementation

### Target file

`scripts/mcp_servers/mdq/health_check.py`

### Procedure

1. Locate `_check_stale_documents()`.
2. Add the nosec annotation to the `f"SELECT COUNT(*) as cnt FROM documents WHERE
   {STALE_SQL_CONDITION}"` line.
3. Line length note: pyproject.toml sets `line-length = 88` but ignores `E501`;
   actual line is 143 chars — ruff does not flag it (confirmed via `uv run ruff check`).

### Method

Direct text edit; no code-structure change.

### Details

Current code (verified this cycle):
```python
def _check_stale_documents(conn: sqlite3.Connection) -> int | None:
    """Check for documents with mtime_ns > indexed_at."""
    try:
        result = conn.execute(
            f"SELECT COUNT(*) as cnt FROM documents WHERE {STALE_SQL_CONDITION}"
        ).fetchone()
        return result["cnt"] if result is not None else 0
    except sqlite3.OperationalError:
        return None
```
Attach the nosec comment to the `f"SELECT ..."` line (line 35).

## Compatibility considerations

Comment-only change; no runtime effect, no SQL logic change.

## Security considerations

Documents (does not change) an existing safe pattern: `STALE_SQL_CONDITION` is a fixed,
module-level string constant, not user-influenced input.

## Rollback considerations

Remove the added comment line; no other rollback steps required.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome | Actual Outcome |
|---|---|---|---|---|
| `scripts/mcp_servers/mdq/health_check.py` | Static (security) | `uv run bandit -r scripts/mcp_servers/mdq/ -c pyproject.toml` | No B608 finding at line 35 | No B608 finding — nosec working |
| `scripts/mcp_servers/mdq/health_check.py` | Static (suppression governance) | `uv run python tools/check_suppression_justification.py scripts/mcp_servers/mdq/health_check.py` | No violations | All checks passed |
| `scripts/mcp_servers/mdq/health_check.py` | Static (lint) | `uv run ruff check scripts/mcp_servers/mdq/health_check.py` | No new findings | All checks passed |
| mdq test suite | Regression | `uv run pytest tests/mcp_servers/mdq/ -v` | No new failures (comment-only change) | Not run — comment-only change |

## Out of scope

`STALE_SQL_CONDITION`/query logic changes; the other 4 target files in this plan.

## Execution Status

### Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | nosec annotation applied on line 35 |
| 2 | Add or update tests per Validation plan | Skipped | — | — | N/A: comment-only change, no new tests required |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | bandit clean, suppression OK, ruff clean |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Skipped | — | — | N/A: no documentation update in scope |

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
- **Generated at**: 20260824-181740
- **Related target files**: `scripts/mcp_servers/mdq/health_check.py`

## Adversarial verification notes (this cycle)

Re-verified line 35's content and confirmed `STALE_SQL_CONDITION`'s definition/import
chain against current source — unchanged since the plan was generated. Confirmed via
`grep -rl "20260823-193604_plan" implementations/ implementations/done/` that no
existing implementation procedure document already covers this plan/target pair. No
blocking unknowns or contradictions found.
