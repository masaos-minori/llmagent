# Reconcile the internal contract of ADR-010

## Priority
High

## Summary
Make `docs/10_adr/adr_02_06_010_rag-fallback.md` describe one current contract. Align Decision, Assumptions, Invariants, Consequences, Failure Policy, and Implementation References without renaming runtime configuration keys or redefining the failure policy.

## Background
Confirmed by reading the current file (Explicit in file):
- Decision Details item 11 and the ragcorpus001 Amendment require corpus identity comparison on every fallback, while Consequences > Negative says "a divergent configuration is not detected" and INV-09 says consistency "is not guaranteed" without mentioning the identity comparison.
- Context and Decision use `rag_query_service_url` (stated as renamed from `rag_service_url`), but INV-01 and the Implementation References entry for `rag_pipeline_models.py` still say `rag_service_url`. The repository code uses only `rag_query_service_url` (Explicit in code: `scripts/rag/pipeline.py`, `scripts/shared/types.py`).
- Decision item 6 includes HTTP 200 with `is_error=true` as a fallback condition; INV-04 omits it. The Fallback Policy names parse errors as prohibiting fallback, consistent with item 9 but pending the failure-policy decision.
- Assumptions say the two modes read separately configured `rag_db_path` values "identical by configuration convention only", while Data Ownership calls `rag.sqlite` "shared by both" modes.

## Problem
Sections of the same ADR describe different revisions of the contract, so an implementer may follow an obsolete statement while reasonably believing it is authoritative. Identity equivalence must also not be overstated as identical search results.

## Reason for Change
An ADR must provide one current architectural contract. It is High because ADR-010 is the sole authority for RAG fallback under ADR-004, and the inconsistencies concern corpus identity and fallback eligibility. The final failure-policy wording must wait for the dependent policy issue.

## Implementation Intent
Edit the ADR so these are separate and consistent: physical database sharing, logical corpus identity, search-result equivalence, current configuration names, and current fallback eligibility. Preserve section structure, invariant identifiers, and anchors. Keep superseded decisions as explicitly historical (for example via the existing Amendment record). Do not redefine the failure policy; take it from the dependent issue's outcome.

## Target Files or Areas
- `docs/10_adr/adr_02_06_010_rag-fallback.md`
- `docs/10_adr/adr_01_index.md` only if a status or summary reference must follow

## Required Changes
- Read the complete ADR and list obsolete or conflicting statements.
- Align Decision, Assumptions, Invariants (INV-01, INV-04, INV-07, INV-09), Consequences, and Failure Policy.
- Rewrite corpus identity statements without promising identical search results.
- State whether physical database sharing is required, optional, or one deployment arrangement.
- Resolve `rag_query_service_url` versus `rag_service_url` using repository evidence; update the INV-01 and Implementation References entries accordingly.
- Synchronize fallback conditions with the outcome of the dependent failure-policy issue.
- Update obsolete implementation references.
- Mark superseded decisions as historical.

## Constraints
- Do not rename runtime configuration keys; this is documentation-only.
- Do not independently redefine the failure policy.
- Preserve section structure, invariant identifiers, and anchors unless a necessary change is explained.
- If the authoritative configuration name is unclear, report the missing evidence rather than choosing arbitrarily.
- Follow `skills/DESIGN.md` Docs content policy; write in English.

## Acceptance Criteria
- All current-contract sections describe the same behavior.
- Corpus identity and search-result equivalence are distinguished.
- Database-sharing assumptions are unambiguous.
- Configuration names are consistent across the document.
- Historical statements cannot be mistaken for current requirements.
- Markdown structure, anchors, and links remain valid.

## Testing Expectations
Not required (documentation-only). Run `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_consistency.py --domain rag`, `check_adr_preservation.py`, `check_adr_structure.py`, `check_adr_invariant_matrix.py`, and `check_docs_japanese.py`. Review the complete document after editing.

## Documentation Impact
Yes, this issue is the documentation change: intent, boundaries, failure behavior, and configuration names in ADR-010, with historical information preserved.

## Out of Scope
- Runtime behavior changes
- New architectural decisions
- Cross-file verification matrix updates

## Dependencies
- Depends on `issues/20261107-050701_adrrag001_rag-fallback-failure-policy.md` for final failure-policy wording. Editorial investigation may begin earlier.

## Unresolved Questions
- Assumption: `rag_query_service_url` is the authoritative name (code evidence); no configuration file sets it, so no deployed-config evidence exists.
- 不明: whether physical sharing of `rag.sqlite` is a requirement or only a deployment arrangement.

## AI Implementation Instruction
Edit only ADR-010 (and an index line only if required). Keep changes minimal and preserve identifiers and anchors. Do not change code or config keys. Stop and report if the authoritative name or sharing assumption cannot be established.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261107-050702
- **Related target files**: `docs/10_adr/adr_02_06_010_rag-fallback.md`
