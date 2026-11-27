## Goal

Create the read-only checker that enforces the classification rule and produces the per-suite report
(REQ-003 — every classified module carries exactly one marker; REQ-004 — the rule is machine-checked;
REQ-005 — CI reports the two suites from one run).

## Scope
**Release unit**: taxonomy mechanism

## Assumptions

- Confirmed in Step 3a: no checker reads pytest markers (`grep -rln "tool.pytest.ini_options" tools/ tests/`
  returns no match), so this is the first reader of the marker data.
- `tools/check_conftest_integrity.py` is the narrow read-only precedent this checker follows, and
  `tools/known_test_failures_baseline.txt` is the baseline-header precedent.
- The checker is a `tools/` script, so it is subject to the tool-inventory gate and the module-size gate
  (`tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt`).
- Requirement sources are the three kinds REQ-002 now names: an Accepted ADR path, a Canonical Source
  Registry entry, or an archived backlog issue path under `issues/done/`.
- Step 3b note (2026-11-27, owner decision): the baseline holds every module in the classified areas that
  carries no taxonomy marker, not only the modules with neither marker nor citation. The Plan's Problem
  section counts 90 "neither signal" modules, but REQ-003's marker obligation covers all 253 modules in
  `tests/agent` and `tests/shared`, so the baseline is 240 entries after the first tranche is excluded.
- Step 3b note (2026-11-27, owner decision): the scan scope is the classified areas (`tests/agent`,
  `tests/shared`) plus any module elsewhere under `tests/` that carries a taxonomy marker, which is what
  keeps the first tranche's `tests/mcp_servers/shell/` row checked while the other areas stay outside the
  baseline.
- Step 3b note (2026-11-27): a citation is read from the module source text as a requirement number
  (`REQ-NNN`), an Accepted ADR path, an archived issue path, or a path registered in
  `config/documentation_canonical_sources.toml`. The checker does not resolve a `REQ-` number against the
  source that recorded it, because that would require a repository-wide scan; the first tranche's existing
  docstring citations (`tests/agent/test_http_lifecycle.py:3`, `tests/mcp_servers/shell/test_shell_mcp_service.py:318`)
  are the form this rule accepts.

## Design decisions

- The classification unit is the test module: `pytestmark` decides the module kind, and only a module that
  mixes both kinds carries per-test markers. The checker reads `pytestmark` and test decorators from the
  AST, not by importing the module, so it stays read-only and cannot execute test code.
- Report mode groups results by the JUnit testcase classname, which is the module, because parametrized
  testcase ids do not match AST-derived ids; grouping by module is also what `tools/compare_test_baseline.py`
  already consumes.
- Exit behavior: rule violations exit 1; in report mode a characterization failure is report-only and a
  contract failure exits non-zero, so the CI step's exit code carries REQ-006 without weakening the gate.
- Step 3b note (2026-11-27): a failure in a module that is in neither suite — a baseline module — is not
  exempted by REQ-006, whose exemption the Plan limits to the characterization marker, so a baseline-module
  failure still exits non-zero. Exit 2 is reserved for a usage or input error, matching
  `tools/compare_test_baseline.py`.

## Alternatives considered

- Directory-based split — rejected by the Plan (UNK-01): it breaks the `tests/` mirrors `scripts/` rule and
  the ADR index citations guarded by `tools/check_adr_invariant_matrix.py`.
- Importing each test module to read its markers — rejected: a module that raises at import time would make
  the checker fail for an unrelated reason, and a read-only checker must not execute test code.

## Implementation
### Target file
`tools/check_test_taxonomy.py` (new)
### Procedure

- Read the registered marker names from `pyproject.toml`'s `[tool.pytest.ini_options] markers`.
- For each test module under `tests/`, read `pytestmark` and per-test decorators from the AST.
- Report: a module with no marker outside the baseline; a `contract` module without a requirement citation;
  a module that claims both kinds at module level; a baseline module that has become classified.
- Step 3b additions (2026-11-27): two further categories are reported, both hard failures —
  `marker-not-registered` (a taxonomy marker used by a module but absent from `pyproject.toml`, which AC-1's
  no-unknown-marker-warning condition requires) and `test-claims-both-kinds` (an individual test carrying
  both markers, which REQ-003's per-test-marker rule cannot resolve).
- Add `--junit-xml <file>` report mode that prints a characterization section and a contract section with
  counts grouped by module.

### Method

- `argparse` with the report mode as an optional flag; the baseline path is a module-level constant pointing
  at `tools/test_taxonomy_baseline.txt`.
- Parsing the baseline follows `tools/known_test_failures_baseline.txt`'s format: comment header, one entry
  per line, `path<TAB>reason`.

### Details

- Keep the module under the `tools/` module-size gate; no new third-party dependency (AST and the standard
  library only).
- `--format json|csv` is not added: the CI step reads the human-readable sections, and the machine-readable
  path is the JUnit XML itself.

## Compatibility considerations

- The 90 currently unclassified modules stay green through the baseline, so the gate does not require a
  one-pass re-marking of the suite.
- `tests/tools/test_run_validation_gates.py` must see a gate for the CI lint command that runs this checker
  (document 05), otherwise that test fails.

## Security considerations

- N/A: read-only over repository files; no subprocess, no network, no write.

## Rollback considerations

- N/A: revert the commit; the baseline file is regenerated from the current suite.

## Validation plan

- Unit — `uv run pytest tests/tools/test_check_test_taxonomy.py -v`: the test row named by this row's
  Related Tests cell is named by four rows, so it is not eligible as a companion and keeps its own document
  (document 08).
- Gate — `uv run python tools/check_test_taxonomy.py`: reports only baseline modules as unclassified, exit 0.
- Report — `uv run pytest tests/ -n logical --cov=scripts --cov-report= --junitxml=report.xml -q` then
  `uv run python tools/check_test_taxonomy.py --junit-xml report.xml`: two sections with counts matching the run.
- Sequence: lint → type → arch → security.

## Completion criteria

- The three rule violations are reported, baseline modules are exempt, mixed modules are detected, and the
  report mode's two sections match the run's counts; the exit code distinguishes a contract failure from a
  characterization failure.

## Out of Scope

- The gate definition (document 05), the CI steps (document 07), and the baseline contents (document 03).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the checker per Procedure/Method/Details | Completed | 20261127-111354 | 20261127-111354 | implemented; six finding categories, AST-only read |
| 2 | Add or update tests per Validation plan | Completed | 20261127-111354 | 20261127-111354 | test row keeps its own document (document 08) tests written under document 08 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261127-111354 | 20261127-111354 | includes the `tools/` module-size gate ruff format/check, mypy, bandit, tools module-size gate pass |

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
- **Requirement ID**: `REQ-003` (classification rule), `REQ-004` (checker), `REQ-005` (per-suite report)
- **Source issue**: `issues/20261119-145310_cliplc012_characterization-test-split.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261126-215529_cliplc012_characterization-test-split.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-232726
- **Related target files**: `tools/check_test_taxonomy.py`