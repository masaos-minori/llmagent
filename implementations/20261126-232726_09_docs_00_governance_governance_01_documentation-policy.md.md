## Goal

Record the test-taxonomy classification rule in the documentation authority model (REQ-002 — the rule is
defined where tests are already `verification-contract`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- Confirmed in Step 3a: `docs/00_governance/governance_01_documentation-policy.md:125` is the
  `verification-contract` row of the Resolution Matrix, and its canonical source kind is
  "`tests/` + the requirement source", which is the wording the rule extends.
- The requirement-source definition is the extended one (ADR, Registry entry, or an archived backlog issue's
  recorded requirement), per the owner decision recorded in the Plan's Assumptions.

## Design decisions

- The rule is written as a constraint on the existing `verification-contract` row rather than as a new claim
  type, so the Matrix keeps one row for test authority.
- The "tests cannot silently redefine requirements" constraint is kept and made operational: a module that
  records observed behavior must not present its assertions as normative.

## Alternatives considered

- A new claim type for characterization tests — rejected: it would duplicate `verification-contract` and
  change the Matrix's decision targets.

## Implementation
### Target file
`docs/00_governance/governance_01_documentation-policy.md`
### Procedure

- Extend the `verification-contract` row's Notes or the paragraph after the Matrix with the classification
  rule: `contract` when the assertions are traceable to a requirement source and the module carries that
  citation, `characterization` otherwise.

### Method

- Name the three accepted requirement-source kinds, and state that a characterization module MUST NOT
  present its assertions as normative.

### Details

- One short paragraph; no change to the other Matrix rows.

## Compatibility considerations

- The docs checkers read the authority model; the wording must keep the row's column structure intact.

## Security considerations

- N/A: documentation-only.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- Static — `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`,
  `check_docs_content_policy.py`, `check_docs_japanese.py`.

## Completion criteria

- The authority model states the rule and the three requirement-source kinds, and the docs checkers report no
  finding.

## Out of Scope

- The task-scope mapping row in `docs/00_index.md` (document 10) and the operational convention in the skill
  (document 11).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the rule text per Procedure/Method/Details | Pending | — | — | |
| 3 | Run the documentation gates named in `rules/tool-gates.md` | Pending | — | — | |

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
- **Requirement ID**: `REQ-002` (classification rule in the authority model)
- **Source issue**: `issues/20261119-145310_cliplc012_characterization-test-split.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261126-215529_cliplc012_characterization-test-split.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-232726
- **Related target files**: `docs/00_governance/governance_01_documentation-policy.md`
