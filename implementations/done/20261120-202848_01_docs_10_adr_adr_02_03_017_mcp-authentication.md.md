## Goal
- Rewrite the two commit-reference history statements in ADR-017 as current-specification statements, keeping every normative claim intact (Plan REQ-001: rewrite the commit references as specification text).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Re-run the Plan AC-1 history search on this file immediately before editing; if a statement is already gone, skip it and record the evidence (source issue AI Implementation Instruction). Verified present on 20261120 (lines 56, 97 cite commit `cad5e91ea`).
- ADR-010 is `Withdrawn` and stays untouched; re-confirm `Withdrawn` in `docs/10_adr/adr_02_06_010_rag-fallback.md` (Plan Reference Files) before touching neighboring ADRs.

## Design decisions
- Rewrite in place rather than delete: the normative claims (fail-closed middleware, no accept-all opt-out, no bypass mode) are part of the accepted decision and must remain present-tense specification text; only the commit citation and past-tense framing are removed.

## Alternatives considered
- Delete both sentences entirely — rejected: it would remove normative content (`no bypass mode is supported`) that the fail-closed decision depends on.

## Implementation
### Target file
- `docs/10_adr/adr_02_03_017_mcp-authentication.md`

### Procedure
- Edit only the two history clauses (line 56 in Decision Details item 4; line 97 in Alternative B Disadvantages). Leave every other line byte-identical.

### Method
- Line 56: drop the sentence "The former test-only bypass was removed (commit `cad5e91ea`);" and keep the specification clause, ending item 4 with "...and no accept-all opt-out exists; no bypass mode is supported."
- Line 97: drop the trailing clause "; the test-only bypass was already removed in commit `cad5e91ea`" so the Disadvantages bullet ends at "...the fail-closed rule exists to prevent."

### Details
- Do not change the Decision, Invariants, Known Deviations, Approval, or any authority/Blocking value; `tools/check_adr_preservation.py` guards them (Plan AC-2).
- If `check_adr_preservation.py` reports an ERROR, revert this file (`git checkout -- docs/10_adr/adr_02_03_017_mcp-authentication.md`) and report a scope amendment instead of forcing the rewrite (Plan Risks mitigation).

## Compatibility considerations
- Docs-only prose edit; the file is consumed by the doc-quality/ADR checkers and `config/adr_authority.toml` does not parse its prose. No consumer changes needed.

## Security considerations
- N/A: prose-only edit; the fail-closed security specification text is preserved.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`; `uv run python tools/check_adr_preservation.py`; `uv run python tools/check_adr_structure.py` (Plan AC-1, AC-2).
- History search re-run: `rg -n -i "moved from|removed on|renamed from|was removed|candidate replacement|grep for" docs/10_adr/adr_02_03_017_mcp-authentication.md` returns no hit; `rg -n "cad5e91ea"` in this file returns no hit.

## Completion criteria
- No commit reference or past-tense removal statement remains in this file; the fail-closed / no-bypass specification wording is intact; `check_adr_preservation.py` reports no ERROR for this file.

## Out of Scope
- Any other ADR file (including `docs/10_adr/adr_02_06_010_rag-fallback.md`, skipped as `Withdrawn`); any change to decision, invariant, or authority data.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261120-205415 | 20261120-205445 | changed docs/10_adr/adr_02_03_017_mcp-authentication.md |
| 2 | Run the validation sequence (`rules/toolchain.md`) with the doc-quality and ADR checkers named in the Validation plan | Completed | 20261120-205536 | 20261120-210851 | stale-detector clean; check_docs_quality Pass; check_adr_preservation Pass exit0 (1 WARNING, no ERROR: Decision text changed; sentence-level mapping: item 4 lost 'The former test-only bypass was removed (commit cad5e91ea);' -> 'exists; no bypass mode is supported.', Alternative B Disadvantages lost '; the test-only bypass was already removed in commit cad5e91ea'); check_adr_structure Pass; check_adr_invariant_matrix Pass; history re-search no hit; full-suite pending batch end |

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
- **Requirement ID**: `REQ-001` (rewrite the ADR-017 commit references as current-specification statements)
- **Source issue**: issues/20261117-123022_adrchk022_history-comment-removal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261120-201816_adrchk022_history-comment-removal.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-202848
- **Related target files**: `docs/10_adr/adr_02_03_017_mcp-authentication.md`