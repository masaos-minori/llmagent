## Goal
Update the two `complete_doc_procedure.py` rows and the `--dry-run` / atomic-write writer
lists in `tools/TOOL_DESCRIPTIONS.md` so the inventory states the tool's `Completed` status,
its `--dry-run` flag, and its atomic writes after the seq 01 and seq 02 code changes land.

## Scope
**Release unit**: N/A: not part of a release unit

Single-file procedure for row 3 of the plan's frozen `Implementation Target Files` table:
`tools/TOOL_DESCRIPTIONS.md` (REQ-005; AC-5). Related check: `tools/check_tool_descriptions_sync.py`.

Documentation-only for this row: no Python change here. This document is the last code-adjacent
step (plan Phase 4) and MUST run after the seq 01 and seq 02 documents' code is in place,
because a description updated before the tool changes would state facts the tool does not yet
have.

## Assumptions
- Plan phase order and seq order differ: this document runs in plan Phase 4, after seq 04
  (tests), seq 02 (constant), and seq 01 (tool change). Do not execute documents in raw seq
  order.
- All line numbers below reference the file before any of this document's edits; the edits
  change row text in place, not the document's section structure.
- The `tools/TOOL_DESCRIPTIONS.md` overlap reported across ten open plans is row-level
  (each plan edits different table rows or paragraphs), not a conflict; the plan dependency
  order keeps the writes sequential.
- The overlap with plans/20261117-134130_wftoolfu002_doc-procedure-archival.md is a
  compatible sequencing dependency: that plan lists this plan's Phases 1 and 3 as its
  prerequisite, so this document lands first.

## Design decisions
- Row division: the summary row (line 108, tool inventory table) gains the written-status word
  so both rows state it (REQ-005 says the file "states the written status"); the detailed row
  (line 255) is rewritten in place to carry the full contract: `Completed` instead of `Done`,
  the `--dry-run` flag, and the atomic-write behavior. The exit-code sentence in that row
  keeps its current meaning because seq 01 preserves exit codes `0`, `1`, `2`.
- Writer lists (line 56 and line 58): `complete_doc_procedure.py` is appended to the
  dry-run writers with a parenthetical noting the dry run also skips the archive move, and the
  atomic-write paragraph's cross-reference `and the six above` becomes `and the seven
  above` so the added writer is covered without duplicating it in the explicit list. This
  keeps one canonical mention per convention instead of listing the tool twice.
- The CLI/exit-code convention paragraph (line 17) is not edited: it already states the
  `main(argv: list[str] | None = None) -> int` entry-point form the tool adopts, and the plan
  does not ask to restate per-tool compliance there.

## Alternatives considered
- Listing `complete_doc_procedure.py` explicitly in both the dry-run list (line 56) and the
  atomic-write list (line 58): rejected as redundant — the atomic paragraph's "the N above"
  reference already includes every dry-run writer, and double listing invites drift.
- Leaving line 108 unchanged because it never named `Done`: rejected; REQ-005 and the plan's
  Phase 4 step say the two rows state the written status, and the plan step counts both rows.

## Implementation
### Target file
`tools/TOOL_DESCRIPTIONS.md` (Modify). The path already exists; no (new) marker.

### Procedure
1. Summary row (line 108): change the parenthetical `(status rows, Verification Findings,
   memo line, archive)` to `(Completed status rows, Verification Findings, memo line,
   archive)`.
2. Detailed row (line 255): change the phrase `Pending` rows to `Done` to the `Completed`
   wording; after the `refusing when the destination exists` clause, add
   that `--dry-run` prints the intended diff and writes, renames, and edits nothing, and that
   the document and memo rewrites go through the shared atomic-write helper named in the
   line 58 paragraph; keep the trailing exit-code sentence unchanged.
3. Dry-run writers paragraph (line 56): append `complete_doc_procedure.py` to the writers
   list with the parenthetical that its dry run also skips the archive move.
4. Atomic-writers paragraph (line 58): change `and the six above` to `and the seven above`.

### Method
- Four in-place text edits; no section, heading, or table-column changes.
- Match the existing row style: one pipe-delimited row per tool in each table, no line breaks
  inside a row, backticked option names and file names as the neighboring rows use them.

### Details
- Line 108 lives in the tool inventory table (columns: file, kind, summary); line 255 lives in
  the detailed behavior table (columns: file, what it touches, behavior).
- The detailed row today reads "sets the `### Execution Status` `Pending` rows to `Done`"; the
  replacement text is "`Pending` rows to `Completed`".
- After step 3 the writer list reads: `module_nodes.py` (`extract`), `set_execution_status.py`,
  `fix_procedure_new_markers.py`, `migrate_runtime_tool_calls.py`, `generate_workitem.py`,
  `fix_docs_section_marks.py`, and `complete_doc_procedure.py` — seven writers, matching the
  step 4 count change.

## Compatibility considerations
- `tools/check_tool_descriptions_sync.py` compares the tables against the live `tools/`
  directory and CI/hook references; both rows keep the tool listed, so the checker must pass
  before and after (AC-5).
- Consumers of the doc are humans and the structure/sync checkers; no code parses these
  paragraphs.
- The description must not be published ahead of the code: this document runs after seq 01 and
  seq 02 (Scope).

## Security considerations
N/A: documentation text edit only.

## Rollback considerations
A single-path `git checkout -- tools/TOOL_DESCRIPTIONS.md` restores the previous inventory; if
the seq 01 or seq 02 code landed in the same push, reverting only this file leaves the doc
describing the old tool — revert scope must match the commit grouping.

## Validation plan
1. `uv run python tools/check_tool_descriptions_sync.py` passes (AC-5).
2. Manual diff review against the post-seq-01 `--help`/docstring of the tool: the row states
   `Completed`, `--dry-run`, and the atomic rewrites, and the writer counts agree (step 4).
3. Full sequence per `rules/toolchain.md`; no pytest target is affected by this file, and the
   full suite is run once in plan Phase 5.

## Completion criteria
- AC-5 holds: the sync checker passes and the two rows plus the two writer lists match the
  tool as implemented by the seq 01 and seq 02 documents.

## Out of Scope
- Editing any Python file (seq 01, seq 02, seq 04 documents).
- The CLI/exit-code convention paragraph (line 17) — see Design decisions.
- Descriptions of any other tool; row-level overlaps with other open plans stay theirs.
- No `docs/*.md` change (this file is under `tools/`) and no deploy step for this row.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261117-205823 | 20261117-205923 | Four in-place edits: summary row parenthetical, detail row (Completed + dry-run + atomic-write wording, exit-code sentence kept), dry-run writer list appended with the archive-move parenthetical, 'the six above' -> 'the seven above'. |
| 2 | Add or update tests per Validation plan | Completed | 20261117-205823 | 20261117-205923 | No test target for this file; check_tool_descriptions_sync.py is its checker (seq 04 module covers the tool's behavior). |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261117-210903 | uv run python tools/check_tool_descriptions_sync.py -> No issues found; rg 'Done' tools/TOOL_DESCRIPTIONS.md reports nothing; writer list counts 7, matching the paragraph. Full sequence deferred to end of batch. Batch-mode validation: ruff format/check, mypy (CI invocation), bandit, lint-imports, ast-grep Not available locally, module-size tools baseline OK, radon, targeted tests, and the full suite twice: run 1 1 failed (tests/rag flaky, unrelated) / 12614 passed, run 2 12615 passed / 7 skipped / 0 failed. coverage xml + diff-cover -> no lines with coverage info (diff is tools/-only, coverage measured on scripts/). |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261117-205923 | N/A: no docs/00_index.md task-scope mapping for tools/TOOL_DESCRIPTIONS.md (this file is the tools inventory itself). |

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
- **Requirement ID**: REQ-005
- **Source issue**: issues/20261117-123331_wftool002_status-vocabulary-unify.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261117-124614_wftool002_status-vocabulary-unify.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261117-180831
- **Related target files**: `tools/TOOL_DESCRIPTIONS.md`