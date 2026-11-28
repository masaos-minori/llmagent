# Implementation Procedure — scripts/mcp_servers/mdq/db_grep.py

## Goal

Return the context grep was asked for, report the line number from the stored `start_line`, support
multiple matches per chunk, and apply the output limit to the context-inclusive text.

## Scope
**Release unit**: grep-context-and-line-numbers

Requirement implemented: REQ-006 (grep returns the requested context, computes line numbers from the
stored `start_line` with the synthetic heading offset, defines multiple matches per chunk and
multiline semantics, honors an explicit zero context, and applies output limits to the
context-inclusive text). Acceptance criterion: AC-5.

## Assumptions
- The reported line is the first stored content line, `start_line + 1 + k` (UNK-03, resolved by the
  owner on 20261127); the number of leading blank lines stripped at index time is not recoverable,
  so the definition is documented rather than reconstructed.
- The context fields are added to `GrepDocMatch` by procedure seq 01; this document fills them.
- Multiple matches per chunk up to the cap and line-anchored multiline semantics are the Plan's
  default pending the owner decision (UNK-05); both are pinned by tests.
- `re.compile(req.pattern)` is called with no flags in `scripts/mcp_servers/mdq/mdq_service.py`, so
  the semantics are stated here rather than changed by adding flags.

## Design decisions
- `line_number` keeps its name and changes meaning: it becomes `start_line + 1 + k`, the
  first-stored-content-line definition, so the reported line is the source-file line for a section
  stored without stripping and the documented definition otherwise. Implemented as
  `start_line + match_line`, where `match_line` is the index within the synthesized
  `heading\ncontent` text: index 0 is the synthetic heading, so a heading-line match reports
  `start_line` and content line k reports `start_line + 1 + k` — the same contract.
- The context becomes part of the result rather than a local variable, so `_context_lines` at Line 39
  is replaced by the returned fields.
- Re-verified 20261128: the limit is applied as a character budget, not as a slice of the joined
  text. `match_text` is truncated at `max_chars` itself; the remaining budget
  (`max_chars - len(match_text)`) is spent on whole context lines, each costing its length plus one
  join newline, taken nearest the match first and alternating sides. Contiguous `start_idx`/`end_idx`
  bounds select the candidate pools; the budget then decides which lines survive, so the rendered
  match text plus returned lines never exceed `max_chars` joined. Context is what shrinks when the
  limit is tight, never a partial line.

## Alternatives considered
- Storing the stripped-line offset at index time so the original file line could be recovered:
  rejected by the owner decision (UNK-03), which keeps the schema unchanged.
- Keeping one match per chunk and documenting it as the contract: rejected, because AC-5 requires
  multiple-match behavior to be defined and tested.

## Implementation
### Target file
`scripts/mcp_servers/mdq/db_grep.py`

### Procedure
Return the computed context, compute the line number from the stored `start_line`, collect every
match in a chunk up to the cap, and apply the limit to the context-inclusive text.

### Method
`find_grep_match()` becomes a match-producing function rather than a single-match function; the
collector and the formatter consume the new fields. No new module-level name is introduced.

### Details
Line references below are against the pre-change file (verified 20261128 against
`git show HEAD:scripts/mcp_servers/mdq/db_grep.py`).
- `find_grep_match()` Lines 18-48: keep `match_line` as the match line index within the stored
  content and report `line_number` as `start_line + 1 + k`; Line 46 currently reports
  `start_idx + 1`, which is the context start rather than the match line. The implemented form is
  `start_line + match_line` over the synthesized `heading\ncontent` text (see Design decisions).
- Lines 37-39: `start_idx` and `end_idx` stay the context bounds; `_context_lines` becomes
  `context_before_lines` (new) and `context_after_lines` (new) on the returned model. The bounds now
  select candidate pools; the budget loop decides which whole lines are returned.
- Line 40: apply `max_chars` to the context-inclusive text, not to the match alone.
- Lines 27-48: iterate every `finditer()` hit instead of returning on the first, so a chunk can
  contribute more than one match up to `max_grep_matches`. `find_grep_match()` returns a
  `list[GrepDocMatch]` (empty when no hit); the name is unchanged.
- `_collect_grep_matches()` Lines 76-95: accept multiple matches per row and stop at the cap.
  Implemented as `matches.extend(...)` followed by a slice to `max_matches` (REQ-006: a single chunk
  can fill the cap).
- `_format_grep_matches()` Lines 98-118: render the returned context lines — context-before lines
  indented before the `Match:` line, context-after lines after it.

## Compatibility considerations
- `line_number` changes value for every grep result, which is a visible tool-output change; the
  pinned assertion in `tests/mcp_servers/mdq/test_db_grep.py` Line 119 (`match.line_number == 4`) is
  rewritten by procedure seq 09 — landed early in the seq 05 cycle (20261128) because the contract
  change is atomic across producer and tests; recorded there.
- `find_grep_match()` changes return type from `GrepDocMatch | None` to `list[GrepDocMatch]`.
  `_collect_grep_matches()` is its only internal caller; test callers are updated by seq 09.
- `GrepDocMatch` gains fields, so the response model changes for API consumers; the change is
  additive.

## Security considerations
- No path or authorization behavior. The reported `source_path` stays the stored value; no absolute
  path is introduced.

## Rollback considerations
- N/A: revert the commit — no persisted state; the model fields revert with procedure seq 01.

## Validation plan
- `uv run pytest tests/mcp_servers/mdq/test_db_grep.py` — returned context, source-file line numbers,
  multiple matches, multiline, explicit zero context, and the limit on context-inclusive text.
- Baseline before any change: 159 passed for the five-file subset, 416 passed and 1 skipped for the
  whole `tests/mcp_servers/mdq/` suite (re-run 20261127).
- As-run 20261128: red phase 14 failed / 7 passed before the implementation; after it
  `test_db_grep.py` = 21 passed, whole `tests/mcp_servers/mdq/` + `tests/mcp_servers/test_mdq_audit.py`
  = 533 passed (was 525 before this cycle).
- Full sequence per `rules/toolchain.md`; `uv run python tools/check_module_size.py` (7595 B of
  24576 B used as of 20261128).

## Completion criteria
- The requested context, including an explicit zero, is returned.
- The reported line matches the source file for a section whose stored content begins at its first
  content line, and matches the documented definition otherwise.
- Multiple matches per chunk are reported up to the cap, and the limit applies to the
  context-inclusive text.

## Out of Scope
- The match model fields themselves (procedure seq 01).
- The context default resolution, which is in `scripts/mcp_servers/mdq/mdq_service.py` (seq 06).
- Adding regex flags; the multiline semantics are stated, not changed.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Pin the current chunk-relative line number, missing context, and one-match-per-chunk behavior | Completed | 2026-11-28 | 2026-11-28 | Pre-change behavior was pinned by the file existing characterization tests (test_only_first_match_in_row_is_returned, test_returns_none_when_no_match, chunk-relative line assertions). They were replaced by the new-contract cases in the same cycle (seq 09 file rewritten early; recorded there). Red confirmed: 14 failed, 7 passed before the implementation. |
| 2 | Return the requested context and the two line fields | Completed | 2026-11-28 | 2026-11-28 | find_grep_match() returns list[GrepDocMatch] with context_before_lines/context_after_lines filled; line_number = start_line + match_line over the heading+content text (heading match reports start_line; content line k reports start_line+1+k, UNK-03). |
| 3 | Support multiple matches per chunk up to the cap | Completed | 2026-11-28 | 2026-11-28 | Every finditer() hit per chunk is returned; _collect_grep_matches() extends the list and slices to max_matches, so one chunk can fill the cap (REQ-006). |
| 4 | Apply the limit to the context-inclusive text and render the context | Completed | 2026-11-28 | 2026-11-28 | max_chars is a budget: match_text truncated at max_chars, remaining budget buys whole context lines nearest-first alternating sides; _format_grep_matches renders context indented around the Match: line. test_db_grep.py = 21 passed. |
| 5 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-28 | 2026-11-28 | Gates: ruff format/check, mypy (20 files), lint-imports 6 kept 0 broken, bandit clean, check_module_size OK (db_grep.py 7595 B). Whole tests/mcp_servers/mdq/ + test_mdq_audit.py = 533 passed (was 525). |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 2 | UNK-03: the line-number offset for a section whose content had leading blank lines stripped at index time is not recoverable from the stored row. Resolved by the owner on 20261127 — the reported line is the first stored content line, so `start_line + 1 + k` is the contract. | Yes | 20261127 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-006 (grep context, line numbers from the stored `start_line`, multiple
  matches, explicit zero, context-inclusive limit)
- **Source issue**: `issues/done/20261119-142125_mdqmcp003_mdq-file-processing-outcomes.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-163030_mdqmcp003_mdq-file-processing-outcomes.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-225351
- **Related target files**: `scripts/mcp_servers/mdq/db_grep.py`
