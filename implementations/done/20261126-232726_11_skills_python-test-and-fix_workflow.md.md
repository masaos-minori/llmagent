## Goal

Record the classification rule in the skill's Test structure section, where the `tests/` mirrors `scripts/`
convention is documented (REQ-002 — the rule is recorded in the convention; REQ-003 — the module-level marker
is the classification unit).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- Confirmed in Step 3a: `skills/python-test-and-fix/workflow.md:24-26` is the Test structure section that
  states the mirror convention.
- The skill is subject to `tools/check_skill_size.py`, so the addition must stay inside the size limit.
- Step 3b correction (2026-11-27, owner decision): the file is already at its recorded ceiling (27339 B), so
  the rule text cannot stay inside it. The ceiling is re-recorded at 27812 B with a dated comment in
  `tools/check_skill_size_baseline.txt`. Moving the rule to an edge-case file does not apply, because the
  classification obligation holds for every test module rather than for a rarely used branch.

## Design decisions

- Three lines: the classification unit (`pytestmark`), the per-test exception for mixed modules, and the
  requirement-citation condition. The operational commands stay in `rules/toolchain.md` (document 06), so the
  skill does not duplicate them.

## Alternatives considered

- N/A: documentation-only row.

## Implementation
### Target file
`skills/python-test-and-fix/workflow.md`
### Procedure

- Add the rule to the Test structure section after the mirror-convention sentence.

### Method

- State the rule as a classification obligation for a test module, not as a checker description.

### Details

- No other section of the skill changes.

## Compatibility considerations

- The skill's existing test-writing steps are unchanged; the rule only adds the marker obligation.

## Security considerations

- N/A: documentation-only.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- Static — `uv run python tools/check_skill_size.py`.

## Completion criteria

- The Test structure section states the rule, and the skill-size check reports no finding.

## Out of Scope

- The authority-model wording (document 09) and the validation sequence (document 06).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the rule to the Test structure section | Completed | 20261127-111354 | 20261127-111354 | rule added to the Test structure section |
| 3 | Run the documentation gates named in `rules/tool-gates.md` | Completed | 20261127-111354 | 20261127-111354 | skill-size check skill-size ceiling re-recorded at 27812 B, owner decision |

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
- **Requirement ID**: `REQ-002` (rule in the convention), `REQ-003` (module-level marker)
- **Source issue**: `issues/20261119-145310_cliplc012_characterization-test-split.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261126-215529_cliplc012_characterization-test-split.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-232726
- **Related target files**: `skills/python-test-and-fix/workflow.md`