# Reduce stale_detector.py false positives on docs-target implementation procedures

## Priority
Medium

## Summary
`scripts/agent/stale_detector.py`'s symbol and line-reference checks
(`_check_symbol_refs()`, `_check_line_refs()`) flagged a false-positive "stale"
mismatch on every one of 22 implementation-procedure documents processed in a single
`code-implementation` batch on 2026-09-20, all of them `docs/*.md`-target procedures.
Each false positive had to be manually investigated and dismissed before Step 3 could
proceed, adding per-file overhead and creating noise that could mask a genuine stale
reference.

## Background
`code-implementation` Step 2.5 (per
`skills/code-implementation/workflow.md`) runs `scripts/agent/stale_detector.py`
against every implementation procedure before allowing implementation to proceed, and
`workflow.md`'s Stale detection result handling section requires aborting execution
immediately on any mismatch — "any single mismatch constitutes 'stale'." This makes
false positives costly: each one must be manually verified as safe to ignore before
continuing, per-cycle, with no persisted record that a given false-positive pattern was
already ruled out in a prior cycle.

## Problem
Two independent false-positive sources were confirmed during the 2026-09-20 batch (22
implementation procedures, all `docs/*.md` targets):

1. **`_SYMBOL_RE` over-matches non-code backtick content** (`_SYMBOL_RE = re.compile(r"`([^`\s]+)`")`,
   line 40; consumed by `_check_symbol_refs()`, lines 267-299). Every backtick-quoted
   token in the procedure document is treated as a candidate source-code symbol,
   including: tool/parameter names from the procedure's own prose (`Edit`,
   `old_string`, `new_string`, `replace_all`, `mypy`, `ruff`, `pytest`, `y`), Markdown
   front-matter field names (`related`, `area`), workflow state values (`Completed`),
   and symbols that genuinely exist but only in a *different* file than the one under
   `## Implementation > Target file` (e.g. `_FIELD_TYPE_TABLE_HEADER_RE` and
   `_RATIONALE_MARKERS`, both real constants in `tools/check_docs_content_policy.py`,
   cited in Design decisions/Alternatives considered prose while the Target file was a
   `docs/*.md` page). The existing filter in `_check_symbol_refs()` (skip `http`-
   prefixed, path-like, or dotted-prefix tokens; line 287's
   `^[a-zA-Z_][a-zA-Z0-9_]*$` pattern) does not exclude any of these categories.
2. **`_check_line_refs()` does not scope a line reference to its own file.** A
   procedure legitimately cites line numbers in a Reference File different from the
   Target file (e.g. "`scripts/agent/llm_turn_runner.py` (lines 149-163)" while the
   Target file is `docs/05_agent_05_llm-and-streaming.md`, which is only 148 lines
   long). `_check_line_refs()` (lines 231-264) compares every "Line N"/"Lines N-M"
   match in the whole document against `len(source_lines)` for the single Target file
   passed to the tool, regardless of which file the citation actually refers to,
   producing a `line_out_of_bounds` false positive.

Both were re-confirmed as false positives during the batch by manually reading the
cited files (e.g. `scripts/agent/llm_turn_runner.py` was confirmed to be 294 lines
with the cited content intact at lines 149-163; `tools/check_docs_content_policy.py`
was confirmed to define `_FIELD_TYPE_TABLE_HEADER_RE`/`_RATIONALE_MARKERS`).

## Reason for Change
Per `AGENTS.md` Loop Prevention and `skills/code-implementation/workflow.md`'s "any
single mismatch constitutes stale" rule, a false positive currently has the same
abort-and-investigate cost as a genuine stale reference. At a 100% false-positive rate
observed across this batch (22/22 procedures), the check provides no signal-to-noise
value for docs-target procedures and risks normalizing "manually verify and proceed"
as a reflexive response that could one day paper over an actual stale reference.

## Implementation Intent
Narrow both checks' false-positive surface without weakening genuine detection:
- For `_check_symbol_refs()`: scope symbol extraction to backtick spans that appear
  inside a `### Target file` / `### Procedure` / `### Method` / `### Details` code
  citation context tied to the *current* Target file, or add an allowlist/heuristic
  excluding known non-symbol prose tokens (tool names used by this repository's own
  workflow vocabulary: `Edit`, `Write`, `Read`, `Bash`, `old_string`, `new_string`,
  `replace_all`; common CLI tool names: `ruff`, `mypy`, `pytest`, `pyright`, `bandit`;
  common front-matter keys: `title`, `area`, `tags`, `related`, `source`; workflow
  status values: `Pending`, `In Progress`, `Blocked`, `Completed`). Consider requiring
  a minimum symbol shape (e.g. `_`-prefixed, `CamelCase`, or `snake_case` with 2+
  underscore-separated segments) to reduce matches on single common words.
- For `_check_line_refs()`: only validate a line-number citation against the Target
  file's own line count when the citation is not immediately preceded/followed (within
  the same sentence or list item) by a different file path — or, more robustly, track
  which file path a line citation is scoped to (the nearest preceding backtick-quoted
  `.py`/`.md` path) and validate against *that* file's line count instead of always
  the Target file's.

## Target Files or Areas
- `scripts/agent/stale_detector.py`

## Required Changes
1. Extend or replace `_check_symbol_refs()`'s filtering (lines 276-288) to exclude
   the tool-vocabulary, front-matter-key, and workflow-status-value categories
   confirmed as false positives above, and/or scope symbol matching to
   Target-file-specific citation contexts.
2. Extend `_check_line_refs()` (lines 231-264) to resolve which file a line citation
   is scoped to and validate against that file's actual line count, rather than
   unconditionally comparing to the Target file's `source_lines`.
3. Re-run the tool against a sample of the 2026-09-20 batch's 22 implementation
   procedure documents (now archived under `implementations/done/20260920-16*.md`) and
   confirm the previously-flagged false positives no longer appear.
4. Add or extend unit tests covering: a tool-vocabulary term in backticks (should not
   flag), a real symbol from a Reference File other than the Target file cited with a
   line number outside the Target file's length (should not flag as
   `line_out_of_bounds`), and a genuinely stale/renamed symbol in the Target file's own
   source (should still flag).

## Constraints
- Do not remove `_check_symbol_refs()`/`_check_line_refs()`'s ability to catch a
  genuinely stale reference to the Target file's own symbols/line ranges — the fix
  must narrow false positives without weakening true-positive detection.
- Per the tool's own design decisions (module docstring), keep using simple
  regex/string matching — do not introduce AST parsing.
- `code-implementation` Step 2.5's "abort on any mismatch" policy is out of scope for
  this issue; only the detector's own accuracy is in scope.

## Acceptance Criteria
- Running `scripts/agent/stale_detector.py` against a procedure document that cites
  `Edit`, `old_string`, `new_string`, `mypy`, `ruff`, `pytest`, or a front-matter key
  (`related`, `area`) in prose reports no `symbol_missing` finding for those tokens.
- Running the tool against a procedure document that cites a real symbol from a
  Reference File (not the Target file) with an accurate line range for that Reference
  File reports no `symbol_missing`/`line_out_of_bounds` finding for that citation.
- Running the tool against a procedure document with a genuinely renamed/removed
  Target-file symbol, or an out-of-bounds line range for the Target file itself, still
  reports the corresponding mismatch.

## Testing Expectations
Unit tests in `tests/agent/test_stale_detector.py` (or the equivalent existing test
file — confirm exact path during implementation) covering the three Acceptance
Criteria cases above. Run `uv run pytest tests/agent/ -k stale_detector -v` (adjust
path as confirmed) plus `uv run ruff check`/`uv run mypy` on the modified file.

## Documentation Impact
N/A: this is an internal tooling accuracy fix with no `docs/00_index.md` task-scope
mapping.

## Out of Scope
- Changing `code-implementation` Step 2.5's abort-on-any-mismatch policy.
- Introducing AST-based parsing (explicitly rejected by the tool's own design
  decisions).
- Any change to the 22 already-archived implementation procedure documents this issue
  cites as evidence.

## Dependencies
N/A: none.

## Unresolved Questions
Whether to implement file-scoped line-citation tracking (more accurate, more complex)
or a simpler suppression heuristic (less accurate, less complex) for `_check_line_refs()`
is an implementation-time design choice — both satisfy the Acceptance Criteria as
stated; leave the choice to whoever implements this issue based on the actual
citation patterns found across a broader sample of `implementations/done/*.md`.

## AI Implementation Instruction
Read `scripts/agent/stale_detector.py` in full before changing it. Preserve its
existing "any single mismatch is stale" contract and simple regex-based design. Add
the exclusion/scoping logic described in Implementation Intent, then verify against
the concrete false-positive examples cited in Problem (available in
`implementations/done/20260920-16*.md` for reference) before declaring the fix
complete. Do not weaken true-positive detection to eliminate false positives — if a
proposed filter would also suppress a genuine mismatch, choose a narrower filter
instead.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260920-175023
- **Related target files**: scripts/agent/stale_detector.py
