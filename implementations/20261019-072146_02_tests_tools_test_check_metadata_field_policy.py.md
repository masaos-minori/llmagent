## Goal

Add unit tests to the new checker's test module `tests/tools/test_check_metadata_field_policy.py`:
an extra front-matter key and an extra workitem section are flagged at `Warning`, a compliant
document/workitem is not, and the current `docs/` and `issues/` corpora yield no false positives.

## Scope

- **In-Scope**: extra-field and compliant fixtures; corpus runs on `docs/` and `issues/`;
  regression assertion on existing tool tests.
- **Out-of-Scope**: changing the checker's behavior.

## Assumptions

- Tests exercise the checker's public functions or invoke its CLI against fixture inputs.
- A small temp directory standing in for `docs/` and `issues/` can supply fixture documents and
  workitems.

## Design decisions

- Follow the patterns of existing `tests/tools/*` so the new tests fit the suite.

## Alternatives considered

N/A: mirroring existing test patterns is the lowest-risk approach.

## Implementation

### Target file

`tests/tools/test_check_metadata_field_policy.py`

### Procedure

1. Scaffold the module following an existing `tests/tools/*` pattern.
2. Front-matter extra-key fixture: a `docs/*.md` front matter with a key outside the schema's
   `properties` (e.g. `foo: bar`) → assert a `Warning` finding (REQ-003).
3. Front-matter compliant fixture: a `docs/*.md` front matter using only permitted keys → assert no
   finding (REQ-005).
4. Workitem extra-section fixture: a workitem with a `## ` section outside its template's canonical
   set → assert a `Warning` finding (REQ-004).
5. Workitem compliant fixture: a workitem using only canonical sections → assert no finding.
6. Corpus runs: run the checker against the current `docs/` and `issues/` corpora → assert zero
   `Warning`s (REQ-006).
7. Regression: confirm existing tool tests still pass.

### Method

- Reuse the sibling test module's conventions (how it builds fixtures, how it invokes the checker,
  how it asserts on `Issue.severity`).
- Assert `issue.severity == "WARNING"` for the extra-key/extra-section cases.
- For the corpus runs, ensure required/template-mandated fields and canonical sections are not
  flagged.

### Details

- `REQ-001`/`REQ-002`: the permitted sets are derived from the schema properties and template
  sections.
- `REQ-003`/`REQ-004`: extra front-matter key / extra workitem section flagged at `Warning`.
- `REQ-005`: required/template-mandated fields not flagged.
- `REQ-006`: corpus runs yield zero `Warning`s.

## Compatibility considerations

N/A: test-only change; does not affect production code or the CI exit contract.

## Security considerations

N/A.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/tools/test_check_metadata_field_policy.py` | Unit | `uv run pytest tests/tools/test_check_metadata_field_policy.py` | Extra key/section flagged at Warning; compliant/corpus clean |

## Completion criteria

- One test each covering the passing and failing path for REQ-003 and REQ-004.
- Corpus runs proving zero `Warning`s on `docs/` and `issues/` (REQ-006).
- The existing tool suites pass unchanged.

## Out of scope

Changing the checker's behavior.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | REQ-001..006 |
| 2 | Add or update tests per Validation plan | Pending | — | — | REQ-001..006 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | all REQs |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | REQ-007 |

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
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-003`, `REQ-004`, `REQ-005`, `REQ-006` (unit + corpus coverage for the metadata field policy checker)
- **Source issue**: `issues/done/20261018-173518_gov016_automate-metadata-field-usage-policy-enforcement.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261018-183121_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-072146
- **Related target files**: `tests/tools/test_check_metadata_field_policy.py`
