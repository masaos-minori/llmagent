## Goal
- Validate the release-unit declaration format in Plans (`REQ-004`: a valid declaration passes, a malformed one fails, a Plan without a unit is unaffected).

## Scope
- In scope: a new declaration check for the `plan` kind, wired into `collect_single_file_findings` and `collect_findings`. Out of scope: procedure documents, the heading check, and output formats.

## Assumptions
- Step 3a: `find_missing_sections`, `collect_single_file_findings`, and `collect_findings` exist; the checker reads only `^## ` headings, so a `### Release units` block adds no section; `collect_findings` and `collect_single_file_findings` currently return only `missing-section` findings.
- No overlap (Step 2): no other Frozen Plan targets this file.
- Depends on row 01: field names `Unit`, `Phases`, `Reason` and the default `N/A: no release unit` are those of the template block.
- Names introduced by this procedure are marked (new).

## Design decisions
- A Plan with no `### Release units` heading, or whose block body is the default `N/A: ...` line, produces no finding. Otherwise each non-blank line must match `**Unit**: {name} | **Phases**: {N, N} | **Reason**: {text}` with all three non-empty; a line that does not match, a missing field, or a phase number that is not a top-level numbered item of `## Implementation steps` yields a finding.
- Category `release-unit`, one finding per bad line, so `render_text`, JSON, and CSV need no change.

## Alternatives considered
- Parsing every `###` block generically was rejected: only the one block is defined.

## Implementation
### Target file
`tools/check_workitem_structure.py`

### Procedure
- Add `find_release_unit_findings` (new) taking the document path and returning finding dicts in the existing shape.
- Add module-level compiled patterns (new): the block heading, the top-level step number, and the entry line.
- Call it from `collect_single_file_findings` and `collect_findings` when the kind is `plan`, appending to the heading findings.
- Update the module docstring and `--help` description with one sentence on the declaration check.

### Method
- Locate the `## Implementation steps` section text (case-insensitive heading, up to the next `^## `), collect phase numbers from `^(\d+)\. ` lines in it, then find `### Release units` inside it and read lines until the next `#` heading.
- Entry check: split on ` | `, require the three bold labels in order with non-empty values, parse phases as comma-separated integers present in the collected set.
- Use `ruff`-clean structure: small helpers, no broad `except`; keep `from __future__ import annotations`.

### Details
- The `### Release units` heading placed outside `## Implementation steps` is a finding (`release-unit`), since the declaration belongs to that section.

## Compatibility considerations
- Plans without the block, and the current template's default text, pass; existing tests of heading detection are unchanged. The tool still exits 1 only when findings exist.

## Security considerations
N/A: read-only text parsing of repository files.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/tools/test_check_workitem_structure.py -v` (row 07 adds the cases).
- Per `routing.md` "Adding a new tool": `uv run ruff format tools/check_workitem_structure.py`; `uv run ruff check tools/check_workitem_structure.py --fix` then without `--fix`; `uv run mypy tools/check_workitem_structure.py`; `uv run bandit tools/check_workitem_structure.py`.
- Smoke test: `uv run python tools/check_workitem_structure.py --file plans/20261102-080336_flowimp002_plan-release-units.md` still reports no findings (a real Plan without a block), and one with the block from a fixture passes.

## Completion criteria
- Valid, malformed (each missing field, unknown phase, misplaced block), and absent declarations behave as stated (AC-3); lint, type, and security checks are clean; `tools/TOOL_DESCRIPTIONS.md` needs no row because no tool is added (run `check_tool_descriptions_sync.py` to confirm).

## Out of Scope
- Checking the procedure `Release unit` line and reading the declaration from `manage_workitem_stage.py` (row 08).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement `find_release_unit_findings` (new) and wire it into both collectors | Completed | 20261102-125310 | 20261102-125310 | Stale clean; 3a anchors confirmed. Changed: tools/check_workitem_structure.py (added find_release_unit_findings, patterns, wiring, docstring/help). render_text wording left unchanged (output formats out of scope) |
| 2 | Add tests (row 07) and run them | Completed | 20261102-125310 | 20261102-125310 | Tests live in row 07's document existing tests/tools/test_check_workitem_structure.py pass; new cases are procedure 07's; manual checks: valid unit passes, unknown phase fails, no-unit plan passes, 0 release-unit findings across all Plans; full suite deferred to plan end |
| 3 | Run the tool lint sequence and the smoke test (`routing.md` Adding a new tool) | Completed | 20261102-125310 | 20261102-125310 | `ruff`, `mypy`, `bandit`, `check_tool_descriptions_sync.py` ruff format/check clean, mypy 1 file clean, bandit 0 issues, check_tool_descriptions_sync clean; smoke test on live flowimp002 Plan: No findings |
| 4 | Update the module docstring and help text | Completed | 20261102-125310 | 20261102-125310 | Documentation lives in the same file docstring and help text updated in the file; no docs/00_index.md mapping |

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
- **Requirement ID**: `REQ-004`
- **Source issue**: issues/20261030-191057_flowimp002_plan-release-units.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261102-080336_flowimp002_plan-release-units.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-085047
- **Related target files**: tools/check_workitem_structure.py