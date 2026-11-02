## Goal
- Make `tools/stale_detector.py` check the companion test files of a procedure with the document: each companion's `(new)` mark and line citations are resolved against that companion, and a document without companions behaves exactly as before (`REQ-004`: companion-aware stale detection).

## Scope
- Modify only `tools/stale_detector.py`: companion parsing, a per-companion check, the `from_procedure` flow, and the module docstring. Medium blast radius (the tool runs in every procedure generation and execution, and `tools/mark_procedure_new_symbols.py` calls it).

## Assumptions
- A1: Step 3a (verified by Read, 2026-11-02): `_TARGET_FILE_SECTION_RE` takes the first backticked path after `### Target file` and `_is_marked_new` reads the marker after it; `from_procedure` then runs `_check_line_refs`, `_check_symbol_refs`, `_check_import_refs`, and `_check_before_blocks` over the whole document text against that one file; `_check_line_refs` already resolves a citation scoped to another path through `_find_scoped_path`; `_new_target_acceptable` reports `new_target_dir_missing` and `new_target_exists`.
- A2: Step 3a: symbol checks are repository-wide for an unscoped symbol (`_symbol_present_somewhere`), so companion test symbols would rarely be false positives, but a companion's `(new)` path, line citations, and `# Before:` blocks would be checked against the target file. That is what this procedure fixes.
- A3: Step 3a: `tools/mark_procedure_new_symbols.py` runs the tool as a subprocess and matches `Symbol '<name>' not found in source` anywhere in a stdout line. A companion mismatch therefore keeps that phrase at the start of its detail and appends a suffix ` (companion {path})`; no prefix is added.
- A4: Overlap judgment (Step 2, `check_plan_target_overlaps.py`, 2026-11-02): this file is also targeted by the archived flowimp007 Plan, whose procedure `implementations/20261102-085029_01_tools_stale_detector.py.md` adds sibling resolution (`resolved`, `warnings` fields; a sibling pass at the end of `from_procedure`; `sibling_mode`). Judged a sequencing dependency, not a conflict (Plan A9): this procedure changes how the document's own target and companions are read first; the sibling pass then runs over the combined mismatch list. Whichever lands second rebases; locate code by symbol name, not line number. The sibling pass resolves names by text and needs no companion awareness.
- A5: The format read is the `seq` 03 template note: `### Companion test files`, then top-level bullets whose first backticked token is the companion path, with an optional `(new)` after it; each bullet's indented lines belong to it.

## Design decisions
- Split the document text: the companion section is removed from the text checked against the primary target (so companion lines are never checked against the target file), and each companion bullet block is checked against its own file. With no companion section the text passed on is the unchanged document text, so output is identical.
- A companion marked `(new)` is validated like a new target (directory exists, file absent) and its unscoped citations are skipped; an existing companion must exist or `source_missing` is reported with the companion's path.

## Alternatives considered
- Check the whole text against every companion: rejected; it would report the target's symbols as missing in test files.

## Implementation
### Target file
`tools/stale_detector.py`

### Procedure
1. Add `_COMPANION_SECTION_RE` (new) and `_COMPANION_BULLET_RE` (new) after `_TARGET_FILE_SECTION_RE`.
2. Add `_parse_companions` (new): return the text with the companion section removed and a list of `(path, declared_new, block_text)`.
3. Add `_check_companion` (new): for one companion, resolve its source path under `source_dir`, apply the new-file or existence rule, run the four existing checks on the block text with `target_file` set to the companion path, and return a `StaleResult` whose mismatch details carry the suffix from A3.
4. In `StaleResult.from_procedure`, after the primary target is resolved, call `_parse_companions` (new), run the existing checks on the returned primary text, then merge each `_check_companion` (new) result with `merge`.
5. Extend the module docstring with a paragraph on companions.

### Method
- `_COMPANION_SECTION_RE` (new): a multiline regex for the line `### Companion test files` through the line before the next heading or the end of text.
- `_parse_companions` (new): split the section on top-level bullet starts with `_COMPANION_BULLET_RE` (new); `declared_new` is `_is_marked_new` at the end of the bullet's path match.
- For an existing companion, `source_missing` detail: `Source file does not exist: {path} (companion {path})`; for a `(new)` companion reuse the `new_target_dir_missing` and `new_target_exists` rules with a companion-specific message through a small wrapper (`_new_target_acceptable` takes the result's `target_file`, so the wrapper sets the message path explicitly instead of changing that function).

### Details
- `result.target_file` remains the primary target; companions never replace it.
- `file_cache` is shared per call so a scoped file is read once.
- Edge case: a malformed companion bullet (no backticked path) is ignored by the parser; the traceability coverage check (seq 05) reports it as not eligible.

## Compatibility considerations
- A document without `### Companion test files` takes the unchanged path: same text, same checks, same output (regression test in seq 08). `to_dict`/`from_dict` and `summary` are unchanged.

## Security considerations
- N/A: read-only; paths are joined under `source_dir` with the existing `lstrip("/")` handling, and the same containment as the target file applies.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/tools/test_stale_detector.py tests/tools/test_mark_procedure_new_symbols.py -v`: all pass (tests in seq 08).
- `uv run ruff format tools/stale_detector.py`; `uv run ruff check tools/stale_detector.py`; `uv run mypy tools/stale_detector.py`; `uv run bandit tools/stale_detector.py`: clean.
- Smoke test on live data: run `uv run python tools/stale_detector.py` on one archived procedure from `implementations/done/` and compare the output with the output before the change (identical).

## Completion criteria
- A document with companions is checked per companion, with `(new)` marks and line citations resolved against the companion (AC-4); a document without companions produces identical output; the four tool checks are clean.

## Out of Scope
- Sibling resolution (flowimp007), changes to `tools/mark_procedure_new_symbols.py`, and the `TOOL_DESCRIPTIONS.md` "Stale detector rules" text (Plan UNK-03).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add companion parsing and the per-companion check, wire them into `from_procedure`, update the module docstring | Completed | 20261102-134150 | 20261102-134150 | added _COMPANION_SECTION_RE, _COMPANION_BULLET_RE, _parse_companions, _check_companion, _suffix_companion (extra tiny helper), wired into from_procedure; docstring; changed: tools/stale_detector.py |
| 2 | Add or update tests per Validation plan (seq 08 procedure) | Completed | 20261102-134150 | 20261102-134150 | tests in seq 08 (135 passed in test_stale_detector, plus 12 mark_procedure_new_symbols) |
| 3 | Run the tool lint sequence (ruff format, ruff check, mypy, bandit) and the live-data smoke test | Completed | 20261102-134150 | 20261102-134150 | ruff format/check, mypy, bandit clean; smoke: all 7922 procedures under implementations/ parse identically (no companion section), synthetic companion doc checked; TOOL_DESCRIPTIONS out of scope (UNK-03); full suite deferred to plan end |

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
- **Requirement ID**: REQ-004 (companion-aware stale detection)
- **Source issue**: issues/20261030-191615_flowimp009_test-row-grouping.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261102-080828_flowimp009_test-row-grouping.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-085649
- **Related target files**: `tools/stale_detector.py`
