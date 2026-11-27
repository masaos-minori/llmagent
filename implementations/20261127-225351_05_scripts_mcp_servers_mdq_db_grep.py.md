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
  stored without stripping and the documented definition otherwise.
- The context becomes part of the result rather than a local variable, so `_context_lines` at Line 39
  is replaced by the returned fields.

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
- `find_grep_match()` Lines 18-48: keep `match_line` as the match line index within the stored
  content and report `line_number` as `start_line + 1 + k`; Line 46 currently reports
  `start_idx + 1`, which is the context start rather than the match line.
- Lines 37-39: `start_idx` and `end_idx` stay the context bounds; `_context_lines` becomes
  `context_before_lines` (new) and `context_after_lines` (new) on the returned model.
- Line 40: apply `max_chars` to the context-inclusive text, not to the match alone.
- Lines 27-48: iterate every `finditer()` hit instead of returning on the first, so a chunk can
  contribute more than one match up to `max_grep_matches`.
- `_collect_grep_matches()` Lines 76-95: accept multiple matches per row and stop at the cap.
- `_format_grep_matches()` Lines 98-118: render the returned context lines.

## Compatibility considerations
- `line_number` changes value for every grep result, which is a visible tool-output change; the
  pinned assertion in `tests/mcp_servers/mdq/test_db_grep.py` Line 119 (`match.line_number == 4`) is
  rewritten by procedure seq 09.
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
- Full sequence per `rules/toolchain.md`; `uv run python tools/check_module_size.py` (5094 B of
  24576 B used).

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
| 1 | Pin the current chunk-relative line number, missing context, and one-match-per-chunk behavior | Pending | — | — | Phase 1, companion seq 09 |
| 2 | Return the requested context and the two line fields | Pending | — | — | REQ-006, Phase 5 |
| 3 | Support multiple matches per chunk up to the cap | Pending | — | — | REQ-006, AC-5 |
| 4 | Apply the limit to the context-inclusive text and render the context | Pending | — | — | REQ-006, AC-5 |
| 5 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
