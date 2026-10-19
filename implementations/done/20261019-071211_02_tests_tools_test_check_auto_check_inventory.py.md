## Goal

Add unit tests to the new checker's test module `tests/tools/test_check_auto_check_inventory.py`:
a documented-but-missing tool is flagged at `Warning`, a valid tool is not, and the current
governance and routing documents yield no false positives.

## Scope

- **In-Scope**: documented-but-missing and valid fixtures; corpus run guard (REQ-004).
- **Out-of-Scope**: changing the checker's behavior.

## Assumptions

- Tests exercise the checker's public functions or invoke its CLI against fixture inputs.
- A small temp directory standing in for `tools/`/`scripts/` can supply existing/absent scripts
  for resolution fixtures.

## Design decisions

- Follow the patterns of existing `tests/tools/*` so the new tests fit the suite.

## Alternatives considered

N/A: mirroring existing test patterns is the lowest-risk approach.

## Implementation

### Target file

`tests/tools/test_check_auto_check_inventory.py`

### Procedure

1. Scaffold the module following an existing `tests/tools/*` pattern.
2. Valid fixture: a documented tool whose basename exists in `tools/`/`scripts/` → assert no
   finding (REQ-003).
3. Documented-but-missing fixture: a documented tool with no matching script → assert a `Warning`
   finding (REQ-003).
4. Drift fixture (optional): a documented tool with only a close candidate → assert a non-blocking
   hint, not a hard failure (UNK-03).
5. Corpus run: run the checker against the current `governance_04` and `routing.md` documents →
   assert zero false positives (REQ-004).

### Method

- Reuse the sibling test module's conventions (how it builds fixtures, how it invokes the checker,
  how it asserts on `Issue.severity`).
- For resolution fixtures, point the checker at a temp tree with a chosen existing/absent script.
- Assert `severity == "WARNING"` for the absent case.
- For the corpus run, ensure differently-named invocations (pre-commit hook names, CI job names)
  are not flagged.

### Details

- `REQ-001`: the parser reads documented tool refs from the authoritative docs.
- `REQ-002`: tool discovery lists `tools/`/`scripts/` dynamically.
- `REQ-003`: a documented-but-missing tool is flagged; a valid tool is not.
- `REQ-004`: corpus run yields zero false positives.

## Compatibility considerations

N/A: test-only change; does not affect production code or the CI exit contract.

## Security considerations

N/A.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/tools/test_check_auto_check_inventory.py` | Unit | `uv run pytest tests/tools/test_check_auto_check_inventory.py` | Absent flagged at Warning; valid/corpus clean |

## Completion criteria

- One test each covering the passing and failing path for REQ-003.
- A corpus run proving zero false positives (REQ-004).

## Out of scope

Changing the checker's behavior.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261019 | 20261019 | Two defects fixed during verification (see procedure 01 Implementation notes): `_path_tokens` missing `line_no`, `Path.sep` AttributeError |
| 2 | Add or update tests per Validation plan | Completed | 20261019 | 20261019 | 17 tests incl. real-corpus zero-finding assertion (REQ-004) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261019 | 20261019 | ruff/mypy/bandit/lint-imports clean; targeted+full suite green; stale-detector benign `new_target_exists` |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261019 | 20261019 | Out of scope (test-only change) |

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
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-003`, `REQ-004` (unit + corpus coverage for the auto-check inventory checker)
- **Source issue**: `issues/done/20261018-173319_gov014_automate-audit-of-auto-checks-documented-as-implemented.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261018-181700_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-071211
- **Related target files**: `tests/tools/test_check_auto_check_inventory.py`
