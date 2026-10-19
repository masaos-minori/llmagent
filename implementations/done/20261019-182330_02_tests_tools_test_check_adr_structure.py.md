## Goal
- Update the fixtures of `tests/tools/test_check_adr_structure.py` to the new ADR file name shape and add a guard over the real ADR files (`REQ-004` (cover the new shape in tests)).

## Scope
- In scope: `tests/tools/test_check_adr_structure.py` only.
- Out of scope: every other file (they have their own procedure documents), ADR content, and historical archives.

## Assumptions
- The Plan's group registry and new names are accepted (Plan Assumptions, UNK-02).
- The 14 renames happen in this one change, so no intermediate state is published.

## Design decisions
- The guard tests read the real directory so a future shape change cannot silently skip ADRs.
- Fixtures keep the ADR ID unchanged and add a group number only, mirroring the real names.

## Alternatives considered
- Keep old-shape fixtures: rejected, because tests would then pass against a tool that cannot read real names.

## Implementation
### Target file

`tests/tools/test_check_adr_structure.py`

### Procedure
1. Rename the fixture `adr_02_999_test.md` (and any other old-shape name) to `adr_02_99_999_test.md`.
2. Add a test that every real `docs/10_adr/adr_02_*.md` matches `_ADR_FILE_RE` (14 files).
3. Add a test that the old shape `adr_02_001_x.md` does not match `_ADR_FILE_RE`.
4. Add a test that `check_section_headings` reports a missing heading for a new-shape fixture, proving the check is not skipped.
### Method
- Edit the 5 existing mentions in place; add the new tests next to the existing `_ADR_FILE_RE` consumers' tests. Run them before the tool change to see the new ones fail.
### Details
- `check_section_headings` and `check_template_residue` `continue` on a non-matching name, so only a positive finding on a new-shape fixture proves the file is processed.

## Compatibility considerations
- N/A: test-only change.

## Security considerations
- N/A: no security impact.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/tools/test_check_adr_structure.py -q`
- `uv run ruff check` and `uv run ruff format --check` on the file, then `uv run mypy` per `rules/toolchain.md`.

## Completion criteria
- Fixtures use the new shape.
- The new tests fail against the old patterns and pass after Phase 2 and Phase 3.

## Out of Scope
- Modifying any file other than the target file; ADR decisions, IDs, status, and invariants; `issues/done/`, `plans/done/`, `implementations/done/`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update fixtures to the new shape | Completed | 20261019-205725 | 20261019-205725 |  |
| 2 | Add the guard and old-shape tests | Completed | 20261019-205725 | 20261019-205725 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261019-205725 | 20261019-205725 | Targeted tests (tests/tools 1049 passed), ruff/mypy/lint-imports pass, doc checkers pass. Full suite NOT run: denied by auto-mode classifier. Pending user decision; not archived. Stale clean. ruff/mypy/lint-imports/bandit ok; tests/tools 1049 passed; full suite (user-run) 9577 passed, 22 skipped; /opt/llm snapshot identical; doc checkers pass. Step 4 full-suite shared across the batch. |

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
- **Source issue**: issues/done/20261019-170548_adrname001_group-adr-file-names-by-theme.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261019-173513_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-182330
- **Related target files**: tests/tools/test_check_adr_structure.py