## Goal
Make ADR-016 state its coverage policy: coverage rules separate from uniqueness rules, the verified current coverage, inclusion criteria, the self-governance decision with a revisit trigger, and what the checkers do and do not cover (REQ-001 to REQ-005).

## Scope
**Release unit**: N/A: not part of a release unit
Edits `docs/10_adr/adr_02_07_016_adr-authority-model.md` only: Decision Details, Verification, and a statement of current coverage. No registry, generated-section, validator, or invariant changes.

## Assumptions
- Phase 1 (facts and structure) needs no owner decision. Phase 2 (inclusion criteria and the self-governance decision) starts only after the owner confirms the Plan recommendation: selective coverage, and no self-governance target now with a revisit trigger (UNK-01, UNK-03). Until then the Phase 2 step stays Pending.
- Overlap with the adrdoc001 Plan is coordination only: that Plan edits governance_01, this one edits ADR-016, and ADR-016 stays the single owner of authority rules. No required order; recorded as compatible.
- Verified now: the registry has 14 targets; ADR-002, ADR-004, ADR-009 and ADR-016 are primary of no target; the ADR contains no coverage language.

## Design decisions
- Split Decision Details item 1 into a coverage item and a uniqueness item without renumbering existing items in a way that breaks references; the registration-duty item references both.
- Describe coverage as selective in practice and not machine-checked; do not copy a per-ADR inventory into the ADR.

## Alternatives considered
N/A: the Plan records the alternatives (comprehensive coverage becomes a separate scope change).

## Implementation
### Target file
`docs/10_adr/adr_02_07_016_adr-authority-model.md`

### Procedure
1. Phase 1: separate coverage from uniqueness in Decision Details and state the verified current coverage; add the Verification note listing what the checkers verify (uniqueness, acyclicity, generated-section drift, front matter consistency) and that coverage is not machine-checked.
2. Phase 2 (after owner confirmation): add the inclusion criteria and record the self-governance decision with rationale and a revisit trigger, without calling a missing self-registration a defect.
3. Phase 3: run `check_adr_authority.py` and the generator check, and record the cycle and assignment results and the candidate unregistered topics in the report, not in the ADR.

### Method
Documentation edit of one file; no tool or registry change.

### Details
- Keep invariant identifiers and text unchanged and the Approval section untouched.
- Candidate unregistered topics (configuration isolation, failure classification, FTS5 text separation) are reported only (UNK-02).

## Compatibility considerations
Documentation only; no registry or checker behavior changes.

## Security considerations
N/A: documentation-only change

## Rollback considerations
N/A: revert the commit

## Validation plan
- `uv run python tools/check_adr_authority.py` and `uv run python tools/generate_adr_authority.py --check`: pass
- `uv run python tools/check_adr_preservation.py`, `check_adr_structure.py`, `check_adr_invariant_matrix.py`: no ERROR
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_japanese.py`: no findings

## Completion criteria
- Coverage and uniqueness are separate Decision Details items; current coverage and the checker limits are stated.
- After owner confirmation: inclusion criteria and the self-governance decision with a revisit trigger are recorded.

## Out of Scope
- Registering additional ADRs or targets; registry, generator or validator changes.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply Phase 1 of Implementation > Procedure (no owner decision needed) | Pending | — | — |  |
| 2 | Apply Phase 2 after the owner confirms selective coverage and no self-governance target (UNK-01, UNK-03) | Pending | — | — | Owner decision pending (UNK-01, UNK-03): do not start until the owner confirms |
| 3 | Run the checkers and record the cycle and assignment results (Phase 3) | Pending | — | — |  |

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
- **Requirement ID**: `REQ-001` to `REQ-005` (coverage statement, separation, inclusion criteria, self-governance decision, verification note)
- **Source issue**: issues/20261107-050706_adrauth001_define-authority-coverage-policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-092627_adrauth001_define-authority-coverage-policy.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-111727
- **Related target files**: `docs/10_adr/adr_02_07_016_adr-authority-model.md`
