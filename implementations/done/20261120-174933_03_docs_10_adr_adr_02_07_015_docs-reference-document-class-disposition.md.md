## Goal
Align ADR-015 Scope with INV-01 by explicit attribution of `tools/generate_adr_authority.py` guard blocks to ADR-016 (owner route, plan REQ-003), record the alignment as a pending amendment, and clear the `check_adr_structure.py` Notes/References drift warning.

## Scope
**Release unit**: ADR015-pending-amendment
- Four edits in one file: Decision Scope attribution sentence, `Related ADRs` entry, `### Approval Record` pending bullet citing AAL-038, and the `## Implementation References` entry that resolves the L126 warning. INV-01 and Verification rows stay unchanged.

## Assumptions
- Owner route (2026-11-20, plan UNK-01 resolved): attribution to ADR-016, not extension of INV-01; both routes are decision changes, so the pending-amendment record is required either way.
- The pending bullet cites AAL-038, which procedure `20261120-174933_04_...governance_03...md` (later row of the same Plan) adds in the same commit — the declared release unit; running this procedure without row 04 fails `tools/check_adr_structure.py`.
- Gated Plan: `tools/plan_dependency_order.py` reports this plan gated (prose) by `issues/20261117-123022_adrchk022_history-comment-removal.md` phase all; the owner chose to proceed with this Plan first (2026-11-20).

## Design decisions
- Attribution sentence placed after the Scope sentence in `## Decision` and mirrored in `## Related ADRs`; ADR-016 Decision 6 (L64) and INV-03 (L124) already govern these blocks, so no new normative obligation is created by this ADR.
- Drift fix adds the exact cited token to `## Implementation References` (`tools/check_adr_structure.py` compares backticked `scripts/`/`tests/` path tokens between the two sections), keeping the Notes text intact.
- Verification finding V3-1 (2026-11-20): the Related ADRs corpus form is plain `- ADR-NNN: description` (ADR-012 L210, ADR-014 L205, ADR-016 L176); a backticked `.md` basename would add a body document reference that `check_docs_structure.py` front-matter coverage would then require in `related:`. Details 2 uses the corpus form without a filename.

## Alternatives considered
- N/A: the Scope-narrowing route was rejected by the owner (plan UNK-01); the rejected route stays recorded in the Plan.

## Implementation
### Target file
- `docs/10_adr/adr_02_07_015_docs-reference-document-class-disposition.md`

### Procedure
1. In `## Decision`, after the sentence "Applies to every document that carries a generated guarded block ... this ADR applies." (L65), add the Scope attribution sentence (Details 1).
2. In `## Related ADRs`, replace `Not applicable` with the ADR-016 entry (Details 2).
3. In `### Approval Record` (under `## Approval`, L160), append the pending bullet (Details 3) after the existing `Current Decision Approval (pending)` bullet citing AAL-017.
4. In `## Implementation References` (L176), add the bullet (Details 4) so the `scripts/agent/*.py` token cited at L126 also appears in References.

### Method
Current-Specification-Only wording; no history comments. Keep INV-01 (L110) and its Verification row byte-identical. The pending bullet follows the ADR-012 form: names the change, states approver/date/scope not recorded, cites the ledger ID, and closes with "No approval is recorded here." Write no approval statement.

### Details
1. Scope attribution sentence: "Guard blocks produced by `tools/generate_adr_authority.py` are governed by ADR-016 (Decision 6 and INV-03); this ADR's INV-01 governs blocks produced by `tools/generate_reference_table.py`."
2. Related ADRs entry: "- ADR-016: Decision 6 and INV-03 govern the `tools/generate_adr_authority.py` guarded sections of the ADR index."
3. Pending bullet: "- **Current Decision Approval (pending)**: Attributing the `tools/generate_adr_authority.py` guard blocks cited by this ADR's Scope to ADR-016 (Decision 6, INV-03) is a decision-text change awaiting maintainer approval; the approver, date, and scope are not recorded, and it is tracked by AAL-038. No approval is recorded here."
4. Implementation References bullet: "- `scripts/agent/*.py` — symbol source of the `agent` and `agent-subpackages` guarded reference tables rendered by `tools/generate_reference_table.py`"

## Compatibility considerations
- ADR-016 already references ADR-015 INV-01 (Decision 6), so the cross-reference is bidirectional; `tools/check_adr_reference.py` and `tools/check_adr_invariant_matrix.py` must stay green.
- Edits are outside guard blocks; both generator `--check` commands must stay clean.

## Security considerations
- N/A: governance attribution only; guard-block enforcement behavior is unchanged.

## Rollback considerations
- Revert together with row 04 (governance_03 AAL-038 entry) as the release unit; a lone revert leaves a dangling AAL-038 reference or an unresolved pending bullet.

## Validation plan
- `uv run python tools/check_adr_structure.py` — 0 errors and no warning for this file (L126 drift warning gone; pending bullet resolves to AAL-038).
- `uv run python tools/generate_reference_table.py --check` and `uv run python tools/generate_adr_authority.py --check` — guard blocks unmodified.
- `uv run pytest tests/tools/test_check_adr_structure.py tests/tools/test_check_adr_invariant_matrix.py -q`.

## Completion criteria
- Every guard-block class in the Scope is covered by INV-01 or explicitly attributed to ADR-016; the pending bullet cites AAL-038 with Approver/Date "Not recorded" and no approval text; the L126 warning no longer fires; guard-block checks clean.

## Out of Scope
- Extending INV-01 to other generators (rejected route); editing ADR-016, the ADR index, or any guarded block; the ledger entry itself (row 04 document).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-11-20 | 2026-11-20 | Gated: issues/20261117-123022_adrchk022_history-comment-removal.md phase all - section-disjoint overlap on ADR-017; owner chose this Plan first (2026-11-20) Implemented with V3-1 (Related ADRs corpus form, no filename backtick) |
| 2 | Land row 04 (AAL-038 ledger entry) in the same commit (release unit ADR015-pending-amendment) | Completed | 2026-11-20 | 2026-11-20 | Gated: issues/20261117-123022_adrchk022_history-comment-removal.md phase all - section-disjoint overlap on ADR-017; owner chose this Plan first (2026-11-20) AAL-038 landed via procedure 04 edits in the same commit unit; joint validators green |
| 3 | Run the documentation checkers named in `routing.md` Tools (Validation plan) | Completed | 2026-11-20 | 2026-11-20 | Gated: issues/20261117-123022_adrchk022_history-comment-removal.md phase all - section-disjoint overlap on ADR-017; owner chose this Plan first (2026-11-20) check_adr_structure: No issues found (L126 warning gone, AAL-038 resolves); gen --check pair clean; 116 tools tests passed |

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
- **Requirement ID**: REQ-003 (align ADR-015 Scope with INV-01 via attribution to ADR-016 and fix the Notes/References drift)
- **Source issue**: issues/20261117-123021_adrchk021_adr-editorial-defects.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261120-172527_adrchk021_adr-editorial-defects.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-174933
- **Related target files**: docs/10_adr/adr_02_07_015_docs-reference-document-class-disposition.md