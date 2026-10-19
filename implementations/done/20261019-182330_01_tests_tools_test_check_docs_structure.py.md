## Goal
- Update the fixtures of `tests/tools/test_check_docs_structure.py` to the new ADR file name shape and add tests that fail on the old shape (`REQ-004` (cover the new shape in tests)).

## Scope
- In scope: `tests/tools/test_check_docs_structure.py` only.
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

`tests/tools/test_check_docs_structure.py`

### Procedure
1. Rewrite every fixture name of the form `adr_02_NNN_*.md` (and `10_adr/adr_02_NNN_*.md`) to `adr_02_GG_NNN_*.md` with a two-digit group, keeping the ADR ID part unchanged.
2. Add a test that `ADR_ID_RE` captures the three-digit ADR ID (not the group) from `adr_02_01_002_platform-config-isolation.md`.
3. Add a test that `check_unique_adr_ids` reports two files with the same ADR ID in different groups as duplicates and accepts distinct IDs.
4. Add a test that the 14 real files under `docs/10_adr/` give 14 unique IDs (after Phase 3 renames).
5. Add a test that an old-shape name `adr_02_001_x.md` is no longer recognised as an ADR by `ADR_ID_RE`.
### Method
- Edit the existing fixture strings in place (17 mentions of the old shape; lines about 291-312, 643-729, and 770 per the Plan). New tests follow the file's existing pytest style (tmp_path-based docs trees). Write the tests first and run them against the unchanged tool to see the new ones fail.
### Details
- The real-files test reads `docs/10_adr/` from the repository, so it fails until Phase 3; run it after the renames. The old-shape test documents the intended break.

## Compatibility considerations
- N/A: test-only change.

## Security considerations
- N/A: no security impact.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/tools/test_check_docs_structure.py -q`
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
| 1 | Update fixtures to the new shape | Completed | 20261019-205723 | 20261019-205723 |  |
| 2 | Add the guard and old-shape tests | Completed | 20261019-205723 | 20261019-205723 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261019-205723 | 20261019-205723 | Targeted tests (tests/tools 1049 passed), ruff/mypy/lint-imports pass, doc checkers pass. Full suite NOT run: denied by auto-mode classifier. Pending user decision; not archived. Stale clean. ruff/mypy/lint-imports/bandit ok; tests/tools 1049 passed; full suite (user-run) 9577 passed, 22 skipped; /opt/llm snapshot identical; doc checkers pass. Step 4 full-suite shared across the batch. |

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
- **Related target files**: tests/tools/test_check_docs_structure.py