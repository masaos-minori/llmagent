## Goal
Add unit tests for the new `eventbus`, `shared`, and `db` domain mapping with a valid and a stale reference (REQ-003: tests for the new mapping).

## Scope
- Add tests to the existing test module that drive `main()` with a temporary docs tree for each new domain.
- No change to the existing tests.

## Assumptions
- `main(argv)` accepts `--docs-dir` for the docs tree but resolves `repo_root` from the real repository, so a fixture doc can cite a real `scripts/` path as the valid reference (verified in `main()`).
- `check_file_path_references` reports a missing `scripts/...` path at WARNING severity and `report_and_exit` returns 0 for warnings only (verified in the library).

## Design decisions
- Use `main()` end to end (capsys for output, return code) rather than calling individual check functions, because the behavior under test is the domain registration.
- Parametrize over the three `(domain, subfolder)` pairs so one test body covers all new domains.

## Alternatives considered
N/A: a table-consistency assertion is added alongside the behavior tests instead of a separate approach.

## Implementation
### Target file
`tests/tools/test_check_docs_consistency_checks.py`

### Procedure
1. Add a helper that creates `docs/<subfolder>/doc.md` under `tmp_path` with given lines and returns the docs dir.
2. Add a parametrized test where the doc cites an existing path (for example `scripts/eventbus/schema.py`): `cdc.main(["--domain", d, "--docs-dir", str(docs)])` returns 0 and prints `No issues found.`
3. Add a parametrized test where the doc cites a nonexistent path (for example `scripts/eventbus/no_such_module.py`): returns 0 and the output has a `[WARNING]` line naming the path.
4. Add a test that the three tables (`DOMAIN_PREFIXES`, `DOMAIN_SUBFOLDERS`, `DOMAIN_GENERIC_CHECKS`) have identical key sets and that the new subfolders match the on-disk folder names.

### Method
- Use `capsys` and `tmp_path`; follow the existing style (module-level functions, type hints, `from __future__ import annotations`).
- Update the module docstring to mention the domain-registration tests.

### Details
- Cite a path that exists in `scripts/` for the valid case so no fixture repo is needed; the stale path must not exist anywhere under `scripts/`.
- Do not assert on the number of findings of the live corpus.

## Compatibility considerations
N/A: test-only addition; existing tests untouched.

## Security considerations
N/A: temporary files only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/tools/test_check_docs_consistency_checks.py -q`; the new tests fail if a domain key is removed from the tool.
- `uv run ruff format`/`check` on the file, `uv run mypy tests/tools/test_check_docs_consistency_checks.py` if pre-commit covers it.

## Completion criteria
- Valid-reference runs return 0 with `No issues found.` and stale-reference runs return 0 with a Warning for each of the three new domains.
- The table-consistency test passes.

## Out of Scope
- Tests for the five existing domains and for domain-specific checks.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the fixture helper and the new tests | Pending | — | — | |
| 2 | Run the new tests against the registered domains | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-003` (unit tests for the new domain mapping)
- **Source issue**: `issues/20261021-101756_domaincov_decide-consistency-check-coverage-for-the-eventbus-and-shared-db-docs-domains.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261022-093304_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-100147
- **Related target files**: tests/tools/test_check_docs_consistency_checks.py
