## Goal
Record the coverage decision for the EventBus, Shared, and DB documents in `governance_04` by replacing the "not covered" statement and extending the domain list and usage examples (REQ-004: record the decision).

## Scope
- Edit the domain list, the statement that `--domain` accepts only five domains, and the usage example block.
- No Verification Matrix row is added.

## Assumptions
- The decision recorded is "covered by the generic checks" (the Plan's recommended default; the owner may overrule it, see the Plan's UNK-01).
- The docs content policy forbids implementation counts, so the new text must not state a number of domains.

## Design decisions
- State the decision as current behavior: the three domains run only the generic checks and have no domain-specific check.
- Avoid the word "five"/counts in the new sentence.

## Alternatives considered
N/A: single-statement docs edit.

## Implementation
### Target file
`docs/00_governance/governance_04_documentation-checks.md`

### Procedure
1. In the domain list add bullets for `eventbus` (EventBus docs vs `scripts/eventbus/`), `shared` (Shared docs vs `scripts/shared/`), and `db` (DB docs vs `scripts/db/`).
2. Replace the sentence "`--domain` accepts only these five domains; there is no EventBus or Shared/DB domain, so those documents are not covered by this check." with a sentence stating that the EventBus, Shared, and DB domains run only the generic checks (links, removed-file references, command drift, file-path references, function references) and have no domain-specific drift check.
3. Add three usage lines for the new domains in the usage example block, aligned with the existing comments.

### Method
- Edit in place with minimal diff; keep the surrounding "Checks performed per domain" list unchanged.
- English only; no literal counts.

### Details
- Do not touch GV-023 or the matrix.
- Re-read the file immediately before editing: it is also targeted by the anchor-validation and glossary Plans of this batch.

## Compatibility considerations
N/A: documentation only.

## Security considerations
N/A: documentation only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_japanese.py`.
- `uv run python tools/check_docs_consistency.py --domain agent` (unaffected domains stay clean).

## Completion criteria
- `governance_04` no longer says the EventBus and Shared/DB documents are not covered.
- The domain list and usage examples include the three new domains and match the tool help.
- Docs checkers pass.

## Out of Scope
- Adding a gate or matrix row; per-domain CI workflows.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the domain list, the decision statement, and the usage examples | Completed | 20261022-103312 | 20261022-103312 | Changed: docs/00_governance/governance_04_documentation-checks.md |
| 2 | Run the documentation checkers named in `routing.md` Tools | Completed | 20261022-103312 | 20261022-103312 | validated; full suite 9687 passed, 14 skipped; docs checkers pass |

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
- **Requirement ID**: `REQ-004` (record the coverage decision in governance_04)
- **Source issue**: `issues/20261021-101756_domaincov_decide-consistency-check-coverage-for-the-eventbus-and-shared-db-docs-domains.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261022-093304_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-100147
- **Related target files**: docs/00_governance/governance_04_documentation-checks.md