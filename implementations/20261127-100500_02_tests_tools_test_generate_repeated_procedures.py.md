## Goal
- Create `tests/tools/test_generate_repeated_procedures.py` to verify `tools/generate_repeated_procedures.py` with a synthetic ten-row Plan and each refusal case (`REQ-001`..`REQ-004`).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the new test module; its own document (not a companion) because `tools/TOOL_DESCRIPTIONS.md` also names it in `Related Tests`.

## Assumptions
- Run after the seq 01 procedure.
- Tests point `tools.generate_workitem.IMPLEMENTATIONS_DIR` and `REPO_ROOT` at `tmp_path` with `monkeypatch.setattr` (the path function reads the module-level constants) and pass the Plan by absolute path under `tmp_path`.

## Design decisions
- Import `import tools.generate_repeated_procedures as grp` and `import tools.generate_workitem as gw`; a `_plan(rows)` helper writes a synthetic Plan with `## Implementation Target Files` rows, a Traceability section with a `Source issue` line, and a template-file helper writes the body (all template headings from `## Goal` through `## Execution Status`, using the placeholders).

## Alternatives considered
- Running against the real repository: rejected, it would create files in `implementations/`.

## Implementation
### Target file
`tests/tools/test_generate_repeated_procedures.py` (new)

### Procedure
1. Happy path: ten rows `config/a01.toml`..`config/a10.toml` with `Change Responsibility` "Add key x to config/aNN.toml" produce ten files; filenames equal those `gw.implementation_procedure_output_path` computes with `seq` `01`..`10` and the Plan's marker timestamp.
2. Sequence parity: for the same Plan, the filenames equal the paths `gw.generate_all_rows` would write (compare with its `--dry-run` output captured via `capsys`).
3. Refusals (each asserts no file under `tmp_path/implementations` and no marker line appended to the Plan): a row with a different `Change Responsibility`; a path that is not a Plan row; a duplicate path; an existing output file (and one under `done/`); a template with a `## Traceability` heading; a template with an unknown placeholder `{other}`.
4. Traceability block: each document ends with the block; `Requirement ID` equals the row's fourth cell, `Source issue` equals the Plan's value, `Related target files` equals the row path.
5. `normalize_change`: path and base name substituted, whitespace collapsed; rows differing only by path are alike; rows with extra words are not.
6. Structure check: a template missing a required heading yields exit 1 and the printed check result; `--dry-run` writes nothing and leaves the Plan byte-identical.

### Method
- `tmp_path` only; subprocess runs of `check_workitem_structure.py` use the real tool on files under `tmp_path`.

### Details
- `rules/coding.md`: line length 88, English comments, annotated helpers.

## Compatibility considerations
- Test-only; `tests/` is rsynced by `deploy/deploy.sh`, which is harmless.

## Security considerations
- N/A: temporary files only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/tools/test_generate_repeated_procedures.py -q`; `uv run ruff format`, `uv run ruff check`, `uv run mypy` on the file.

## Completion criteria
- AC-1 to AC-6 of the Plan are each covered by a passing test; the file passes ruff and mypy.

## Out of Scope
- Changes to `tools/generate_repeated_procedures.py` beyond what a failing test proves necessary (an amendment of the seq 01 procedure).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create `tests/tools/test_generate_repeated_procedures.py` per Procedure | Pending | — | — | Needs seq 01 first |
| 2 | Run the tests and fix failures in the test or report a tool defect | Pending | — | — | |
| 3 | Run ruff and mypy on the file | Pending | — | — | |

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
- **Requirement ID**: `REQ-001`..`REQ-004` (behaviors under test)
- **Source issue**: issues/20261126-151442_wfeff007_repeated-row-procedures.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261127-095809_wfeff007_repeated-row-procedures.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-100500
- **Related target files**: `tests/tools/test_generate_repeated_procedures.py`
