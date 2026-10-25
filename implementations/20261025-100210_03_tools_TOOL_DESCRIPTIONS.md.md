# Procedure: `tools/TOOL_DESCRIPTIONS.md`

Stage-2 output for Issue 20261023-173506 / Plan 20261025-090535. Source plan:
`plans/done/20261025-090535_ci001_scheduled-ci-result-check-that-routes-failures-to-the-test-and-fix-workflow.md`.
Frozen decisions are copied from the plan; this procedure does not re-decide any of them.

**Correction note (2026-10-25, execution cycle):** the originally generated version of this
document belonged to a different design lineage: it cited a nonexistent issue
(`20261024-105844`) and requirements doc (`doc0001`), anchored the new row next to a
nonexistent `tools/check_test_deps.py`, claimed an index-table format with `tools/`-prefixed
paths (the real rows use backticked bare filenames), and stated a gh allowlist
(`run list --failed`, `run view --comments`, `--max-annotations`) that contradicts the Plan's
frozen allowlist (`run list`, `run view`, Plan REQ-004). The user approved rewriting it to
match the Plan and the landed row 1 implementation; this is that rewrite.

**Row:** 3 of 4, Type `Doc`, Path `tools/TOOL_DESCRIPTIONS.md`, Action `Update`, Size `S`, Depends on `tools/check_ci_results.py`

## Goal

- Register the new tool in `tools/TOOL_DESCRIPTIONS.md` — Plan `REQ-007` (AC-6): add the
  `check_ci_results.py` index row and bump the module count, so
  `tools/check_tool_descriptions_sync.py` passes again.

## Scope

- **In-Scope**: two coordinated edits in one file — the `## Index` header count and one table
  row.
- **Out-of-Scope**: any other section of the file; changes to `tools/check_ci_results.py`
  (already landed, row 1) or to `rules/toolchain.md` (row 4).

## Assumptions

- Pre-change state confirmed 2026-10-25: header reads `## Index (53 modules)` (`:15`); the
  Index table spans `:17`..`:71` with exactly 53 data rows; rows use
  `` | `name.py` | Category | Purpose | `` with backticked bare filenames.
- `tools/check_ci_results.py` is currently undocumented: `check_tool_descriptions_sync.py`
  fails with exactly `check_ci_results.py: exists in tools/ but is not mentioned in
  TOOL_DESCRIPTIONS.md` (run 2026-10-25, exit 1). The checker cross-checks backticked `*.py`
  names anywhere in the file, not the index position or the count.
- Category choice `Test`: matches the file's existing rows for test-facing checkers
  (`check_mock_patch_targets.py`, `check_conftest_integrity.py`); the Plan fixes no category
  vocabulary, so the file's own live categories decide.

## Design decisions

- Insert the new row directly after `check_conftest_integrity.py` (`:46`), the file's most
  compact `Test`-category block, keeping the row style one line long like its neighbors.
- Bump the count to 54; after the edit the Index table must contain exactly 54 data rows
  (the count is a prose claim a later staleness review pass can re-verify).
- The Purpose column states the tool's real contract as landed in row 1: allowlisted
  `gh run list` / `gh run view`, per-run failed-test identifiers, repeat grouping over the
  examined window, stdout-only report, exit codes `0`/`1`/`2`.

## Alternatives considered

- Writing a full per-tool description section (as the contaminated draft proposed): rejected —
  the Plan's target row says "Add the new tool's index row and bump the module count", the
  sync checker needs only the name mention, and per-tool prose sections exist only for some
  domains; a single index row is the minimal truthful registration.

## Implementation
### Target file
- `tools/TOOL_DESCRIPTIONS.md`

### Procedure
1. Change `## Index (53 modules)` to `## Index (54 modules)`.
2. Insert one row after the `check_conftest_integrity.py` row:
   `` | `check_ci_results.py` | Test | Read-only CI result reporter: queries recent runs through a fixed gh read-only allowlist (`run list`, `run view`), groups tests that failed in two or more examined runs, and reports red runs, repeats, and a `python-test-and-fix` pointer on stdout; exit `0`/`1`/`2` | ``

### Method
- Direct Markdown table edits; no script generates this content.

### Details
- The row text must not claim a schedule exists (the recurring task is Plan Phase 3,
  user-gated, `UNK-03`/`UNK-05`); it describes the tool only.

## Compatibility considerations

- `check_tool_descriptions_sync.py` is wired into pre-commit; this row is what turns its
  current failure (row 1's new file) green again.

## Security considerations

- None beyond documentation accuracy: the allowlist summary in the Purpose column matches the
  enforcement point in `tools/check_ci_results.py` (`_ALLOWED_VECTORS`).

## Rollback considerations

- Revert the two edits; the sync checker would flag the missing row again (a safe failure mode).

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `tools/TOOL_DESCRIPTIONS.md` | plan AC-6 gate | `uv run python tools/check_tool_descriptions_sync.py` | Exit 0, no findings |
| `tools/TOOL_DESCRIPTIONS.md` | count guard | count the Index table data rows between the `## Index` header row and the next `##` heading, and compare with the header's number | 54, equal to the header claim |

## Completion criteria

- AC-6: the sync checker passes with the new row (Plan `:90`).
- Header count equals the actual Index data-row count.

## Out of Scope

- Scheduling or operational notes (row 4); any change to the tool itself.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply the two coordinated edits to `tools/TOOL_DESCRIPTIONS.md` | Completed | 2026-10-25 | 2026-10-25 | header 53->54 plus one Test-category row after check_conftest_integrity.py |
| 2 | Run the sync checker and count guard | Completed | 2026-10-25 | 2026-10-25 | sync checker exit 0 (was 1 pre-edit); Index data rows counted 54 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | None | N/A | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: code-implementation (procedure corrected in-cycle per user approval)
- **Requirement ID**: `REQ-007` (tool registration)
- **Source issue**: issues/20261023-173506_ci001_scheduled-ci-result-check-that-routes-failures-to-the-test-and-fix-workflow.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261025-090535_ci001_scheduled-ci-result-check-that-routes-failures-to-the-test-and-fix-workflow.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261025-100210 (rewritten 2026-10-25 in the execution cycle)
- **Related target files**: `tools/TOOL_DESCRIPTIONS.md`
