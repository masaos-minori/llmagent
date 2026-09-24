## Goal
Fix both duplicated occurrences of `tests/tools/test_check_docs_quality.py`'s `_KNOWN_DEFECT_PATH` constant — currently `_DOCS_DIR / "90_shared_02_02_types_and_protocols-tool-and-execution-dto.md"` — to `_DOCS_DIR / "40_shared" / "90_shared_02_02_types_and_protocols-tool-and-execution-dto.md"`, per Plan `plans/20260924-150508_plan.md` REQ-003.

## Scope
- In scope: rewriting the `_KNOWN_DEFECT_PATH` definition at both its occurrences (lines 272-274 and 282-284, pre-fix line numbers, confirmed via `grep -n` during Plan creation and revalidation).
- Out of scope: deduplicating the surrounding duplicated fixture block itself (the `_ROOT_DIR`/`_DOCS_DIR`/`_KNOWN_DEFECT_PATH` block appears twice verbatim in the file under two identical `# Fixtures` section headers) — confirmed as a genuine pre-existing structural duplication unrelated to this Plan's own file-move scope, not touched here; seq 04 (the linked file's own move into `docs/40_shared/`, a prerequisite for `test_true_positive_known_defect_case` to actually pass rather than skip, though not a prerequisite for this text edit itself).

## Assumptions
- `test_true_positive_known_defect_case`'s own guard (`if not _KNOWN_DEFECT_PATH.exists(): pytest.skip(...)`) at lines 368-370 and a second usage at lines 491-492/501 reference the `_KNOWN_DEFECT_PATH` variable, not the hardcoded string directly — so fixing the 2 definitions alone is sufficient; no other line requires editing.
- Both `_KNOWN_DEFECT_PATH` definitions (lines 272-274, 282-284) hold byte-identical values today — confirmed via Read during Plan creation — so applying the identical fix to both preserves that symmetry rather than introducing a new divergence.

## Design decisions
Fix both duplicated definitions with the identical target-path change, rather than removing one — deduplicating the block is a separate, unrelated code-quality concern (see Out of scope) that this Plan does not request and that touching here would exceed this row's single-file, single-purpose scope (`skills/python-design` guidance: match the fix's blast radius to the actual defect, not adjacent code smells).

## Alternatives considered
Removing the duplicate block entirely (keeping only one `_KNOWN_DEFECT_PATH` definition) was considered, but rejected: `AGENTS.md` Global Rule 5 scope discipline confines this row to the path-value fix REQ-003 specifies; removing a redundant block is an unrelated refactor with its own blast radius (verifying no other code in the file's remaining structure depends on the duplicated `# Fixtures` header appearing twice) that was not investigated and is not requested by the Plan.

## Implementation
### Target file
`tests/tools/test_check_docs_quality.py`

### Procedure
1. Locate both definitions with `grep -n "_KNOWN_DEFECT_PATH" tests/tools/test_check_docs_quality.py` — expect definitions at lines 272 and 282 (each a 3-line `_KNOWN_DEFECT_PATH = (...)` statement) plus usage sites at lines 368-371 and 491-501 (unaffected, since they reference the variable).
2. Edit the first occurrence (lines 272-274):
   ```python
   _KNOWN_DEFECT_PATH = (
       _DOCS_DIR / "90_shared_02_02_types_and_protocols-tool-and-execution-dto.md"
   )
   ```
   →
   ```python
   _KNOWN_DEFECT_PATH = (
       _DOCS_DIR / "40_shared" / "90_shared_02_02_types_and_protocols-tool-and-execution-dto.md"
   )
   ```
3. Edit the second occurrence (lines 282-284) with the identical change (use a distinct enough surrounding context, or address both via one `replace_all` Edit call given both blocks are byte-identical before the fix).
4. Re-run `grep -n "_KNOWN_DEFECT_PATH" tests/tools/test_check_docs_quality.py` and confirm both definitions now include the `"40_shared"` path component.

### Method
Two text substitutions via Edit (`replace_all: true` is applicable here since the pre-fix text of both occurrences is byte-identical and the post-fix text should also be byte-identical — confirmed via Read during Plan creation that no other code in the file contains this exact 3-line pattern).

### Details
- Confirmed via `grep -n "_KNOWN_DEFECT_PATH" tests/tools/test_check_docs_quality.py`: the constant is defined twice (lines 272, 282), each within its own `# Fixtures` section (lines 266-268 and 276-278 respectively), both with identical `_ROOT_DIR`/`_DOCS_DIR`/`_KNOWN_DEFECT_PATH` assignment bodies.
- `test_true_positive_known_defect_case` (uses `_KNOWN_DEFECT_PATH` at lines 368-371) and a second test (uses it at lines 491-501) both reference the module-level variable, not a hardcoded string — so both tests pick up the fix automatically once the 2 definitions are corrected.

## Compatibility considerations
Before this fix, once seq 04 moves the target file, `_KNOWN_DEFECT_PATH.exists()` would return `False` and both dependent tests would silently `pytest.skip(...)` rather than exercising the known `## 7c.` duplicate-heading regression — this fix restores actual test execution against the file's new location.

## Security considerations
N/A: a test-fixture path constant edit has no security surface.

## Rollback considerations
Revert both edits via Edit back to the flat-path value if needed before commit; after commit, `git revert` the commit that performed this fix.

## Validation plan
- `uv run pytest tests/tools/test_check_docs_quality.py -q` passes (AC-4).
- `uv run pytest tests/tools/test_check_docs_quality.py -k test_true_positive_known_defect_case -v` shows the test actually executing (not skipped) once seq 04's move has landed.
- `grep -n "_KNOWN_DEFECT_PATH" tests/tools/test_check_docs_quality.py` confirms both definitions include `"40_shared"`.

## Completion criteria
Both `_KNOWN_DEFECT_PATH` definitions point at `docs/40_shared/90_shared_02_02_types_and_protocols-tool-and-execution-dto.md`, and `test_true_positive_known_defect_case` executes its assertions (rather than skipping) once seq 04's move has landed.

## Out of scope
Deduplicating the repeated `# Fixtures` block itself; seq 04 (the linked file's own move, a prerequisite for the tests to actually run against real content rather than skip).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20260924-170036 |  |
| 2 | Add or update tests per Validation plan | Completed | — | 20260924-170036 | N/A: this row edits the test fixture itself; no additional test is added |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20260924-170036 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20260924-170037 | N/A: this row's own edit is a test-fixture fix, not a documentation change |

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
- **Requirement ID**: REQ-003
- **Source issue**: issues/20260923-141137_docsreorg09_move-general-shared-docs-into-new-shared-folder.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260924-150508_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260924-151506
- **Related target files**: tests/tools/test_check_docs_quality.py