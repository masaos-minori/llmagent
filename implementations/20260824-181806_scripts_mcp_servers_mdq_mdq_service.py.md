## Goal

Add em-dash-delimited `# nosec B608 — <justification>` annotations to the two bandit
B608 false positives in `scripts/mcp_servers/mdq/mdq_service.py` (lines 209 and 340),
so bandit no longer flags either line. No change to SQL logic.

## Scope

- In scope: `scripts/mcp_servers/mdq/mdq_service.py:209` (the `outline()` method's
  `conn.execute(f"SELECT ... FROM chunks c WHERE {where_clause} ...", params)` call)
  and `:340` (the `_check_stale_document` / status-reporting path's
  `conn.execute(f"SELECT COUNT(*) as cnt FROM documents WHERE
  {STALE_SQL_CONDITION}")` call).
- Out of scope: any change to `where_clauses`/`params` construction or
  `STALE_SQL_CONDITION`; the other 4 target files in the same plan.

## Assumptions

- Line 209: `where_clauses` (`outline()` method) is built only from fixed string
  literals (`"c.source_path = ?"`, `"c.heading_level <= ?"`) joined by `" AND "` —
  confirmed by reading the surrounding method in full; all variable values (`str(p)`,
  `max_depth`) are appended to `params` and bound via `?`, never interpolated into the
  SQL text.
- Line 340: `STALE_SQL_CONDITION` (`scripts/mcp_servers/mdq/mdq_models.py:313`) is the
  same fixed module-level string constant used at `health_check.py:35` — confirmed via
  `grep -rn "STALE_SQL_CONDITION" scripts/mcp_servers/mdq/`.
- The em-dash character (U+2014, `—`) is mandatory for
  `tools/check_suppression_justification.py` — same basis as the sibling procedure
  documents in this batch.
- Re-verified against current source (this cycle): both line numbers and content still
  match the plan exactly — no drift since generation.

## Design decisions

- Line 209: append `  # nosec B608 — where_clauses fragments from fixed constants;
  values bound via params`.
- Line 340: append `  # nosec B608 — STALE_SQL_CONDITION is a fixed string constant`
  (identical justification text to the sibling `health_check.py` annotation, since both
  reference the same constant).

## Alternatives considered

- None beyond the annotation-only approach for either location.

## Implementation

### Target file

`scripts/mcp_servers/mdq/mdq_service.py`

### Procedure

1. Locate the `outline()` method; add the nosec annotation to the `f"SELECT ... FROM
   chunks c WHERE {where_clause} ..."` line (209).
2. Locate the status/stale-count reporting method containing line 340; add the nosec
   annotation to the `f"SELECT COUNT(*) as cnt FROM documents WHERE
   {STALE_SQL_CONDITION}"` line.
3. Confirm line length ≤ 88 chars after each edit; both lines already exceed 88 chars
   pre-existing (long column lists / f-string) — attach each comment to the line's
   existing closing token rather than reflowing the SQL text.

### Method

Direct text edit at both locations; no code-structure change.

### Details

Location 1 (verified this cycle, `outline()`, line ~209):
```python
where_clauses = ["c.source_path = ?"]
params: list[str | int] = [str(p)]
if max_depth is not None:
    where_clauses.append("c.heading_level <= ?")
    params.append(max_depth)
where_clause = " AND ".join(where_clauses)
rows = conn.execute(
    f"SELECT c.chunk_id, c.heading, c.heading_level, c.heading_path, c.start_line, c.end_line FROM chunks c WHERE {where_clause} ORDER BY c.heading_level, c.ordinal",
    params,
).fetchall()
```

Location 2 (verified this cycle, line 340):
```python
stale_count = conn.execute(
    f"SELECT COUNT(*) as cnt FROM documents WHERE {STALE_SQL_CONDITION}"
).fetchone()["cnt"]
```

## Compatibility considerations

Comment-only change at both locations; no runtime effect, no SQL logic change.

## Security considerations

Both annotations document (do not change) existing safe patterns: fixed
string-literal/constant SQL fragments with all variable values bound via `?`/`params`.

## Rollback considerations

Remove the two added comment lines; no other rollback steps required.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/mcp_servers/mdq/mdq_service.py` | Static (security) | `uv run bandit -r scripts/mcp_servers/mdq/ -c pyproject.toml` | No B608 finding at lines 209 or 340 |
| `scripts/mcp_servers/mdq/mdq_service.py` | Static (suppression governance) | `uv run python tools/check_suppression_justification.py scripts/mcp_servers/mdq/mdq_service.py` | No violations |
| `scripts/mcp_servers/mdq/mdq_service.py` | Static (lint) | `uv run ruff check scripts/mcp_servers/mdq/mdq_service.py` | No new findings |
| mdq test suite | Regression | `uv run pytest tests/mcp_servers/mdq/ -v` | No new failures (comment-only change) |

## Out of scope

`where_clauses`/`params`/`STALE_SQL_CONDITION` logic changes; the other 4 target files
in this plan; the pre-existing line-length of both flagged lines (not introduced by
this change).

## Execution Status

### Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details (both locations) | Pending | — | — | |
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
- **Generated at**: 20260824-181806
- **Related target files**: `scripts/mcp_servers/mdq/mdq_service.py`

## Adversarial verification notes (this cycle)

Re-verified both line 209 and line 340 content against current source — unchanged
since the plan was generated. Confirmed `where_clauses` at line 209 is built only from
fixed string-literal fragments (no f-string-interpolated variable content). Confirmed
via `grep -rl "20260823-193604_plan" implementations/ implementations/done/` that no
existing implementation procedure document already covers this plan/target pair. No
blocking unknowns or contradictions found.
