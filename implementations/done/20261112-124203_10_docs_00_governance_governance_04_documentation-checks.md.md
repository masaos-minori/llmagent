## Goal
Describe the extended GV-018 table pattern, the new custom rules, and the Known Deviation check in `governance_04`, including that free-text contradictions are covered only by lexical signatures (`REQ-007` / `AC-7`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Custom-rules paragraph at lines 39-40, the GV-018 matrix row at line 297 (its prose at line 161), and the GV-022 enforcement text at line 177 with its matrix row at line 301 (verified 2026-11-12). Describe only the rules that remain: the plan-ID rule is not kept (row 04 Assumptions), so it must not appear here.
- Execute last, after rows 01 to 06 settle which rules are kept.

## Design decisions
- State intent, scope, and failure behavior; list the rule names; state the limit in one sentence.

## Alternatives considered
N/A: the Plan fixes the approach for this row.

## Implementation
### Target file
`docs/00_governance/governance_04_documentation-checks.md`

### Procedure
1. Update the Custom rules paragraph with the kept rules.
2. Update the GV-018 row (File/Module header shape).
3. Update GV-022 for the bullet-without-ID ERROR.

### Method
- No tool output copied; cite the rule file and tools by path.

### Details
- Limit sentence: free-text contradictions are detected only by the lexical signatures listed; a semantic comparison is out of scope.

## Compatibility considerations
N/A: documentation-only change; no code, config, or schema impact.

## Security considerations
N/A: no authorization, secret, or trust-boundary change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_japanese.py` — pass.

## Completion criteria
- The document describes the kept rules, the widened pattern, the new Known Deviation check, and the lexical-only limit.

## Out of Scope
- Changing governance rule IDs or severities.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261112-221159 | 20261112-223048 | Custom-rules paragraph, section 9 GV-018 prose and row, and section 11 GV-022 prose and row updated; no plan-ID rule described; wording deliberately avoids self-matching the new lexical patterns (first draft triggered 3 self-findings, reworded); deviation: the file passed its recorded 25281-byte ceiling, so SIZE_EXCEPTIONS was re-accepted at 26711 with a dated comment in tools/check_docs_structure.py (repo's documented mechanism, precedent adrauth001 and adrrev010) and its tools baseline row re-recorded 29654 -> 29922; check_docs_quality, check_docs_structure, check_docs_content_policy --strict, check_docs_japanese all pass; full suite 12167 pass |
| 2 | Run the documentation checkers per Validation plan | Completed | 20261112-223049 | 20261112-223049 | Executed and validated 2026-11-12; governance text describes kept rules only |

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
- **Requirement ID**: `REQ-007` — describe the extended checks and the lexical-only limit
- **Source issue**: issues/20261109-113351_adrrev018_docs-checker-harden.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-111505_adrrev018_docs-checker-harden.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-124203
- **Related target files**: `docs/00_governance/governance_04_documentation-checks.md`
