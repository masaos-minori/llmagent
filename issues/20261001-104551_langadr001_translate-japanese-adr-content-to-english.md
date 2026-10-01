# Translate Japanese ADR content to English

## Priority
Medium

## Summary
Most ADRs under `docs/10_adr/` are written largely in Japanese, including their titles. This violates the documentation output-language rule that all files under `docs/` are English with no exception. Translate the ADR titles, front matter, and bodies, plus `docs/10_adr/adr-index.md`, into English without changing their normative meaning.

## Background
- `skills/DESIGN.md` Output language: "All files under `docs/` are English, with no exception, regardless of chat language." `Documentation only`
- `uv run python tools/check_docs_japanese.py` (2026-10-01) lists 15 files in `docs/10_adr/` that contain Japanese characters: ADR-001 to ADR-010, ADR-012 to ADR-015, and `adr-index.md`. Counting lines with Japanese characters per file shows that ADR-001 to ADR-010 and ADR-014 have roughly 100 to 300 such lines each, while ADR-012, ADR-013, ADR-015, and `adr-index.md` have fewer than 30 each. `Explicit in code`
- ADR titles in Japanese are copied into link descriptions in many area guides, for example "SQLiteを4DBへ分離する" for ADR-008.
- Five ADRs also exceed the `check_docs_structure.py` size limit: ADR-002, ADR-003, ADR-004, ADR-006, and ADR-008. Japanese characters take 3 bytes each in UTF-8, so translation may also affect file size. `Explicit in code`

## Problem
- Normative architecture decisions are stored in a language that the rule forbids for `docs/`.
- AI agents and English-only tooling get inconsistent text: the governance and area docs are English, but the ADRs they defer to are mostly Japanese.

## Reason for Change
- ADRs are the canonical source for architecture decisions. Their language must follow the project rule so that every consumer reads them reliably.

## Implementation Intent
- Translate one ADR per change, or a small batch per change, so each translation can be reviewed for semantic fidelity against the original.
- Keep all decision content, invariant IDs (for example INV-xx), statuses, dates, section structure, and identifiers exactly as they are. Translate only prose.
- Translate the titles in front matter and H1, and update `adr-index.md` to match.
- Do not change any decision while translating. If you find an ambiguity or inconsistency, register it under the governance process instead of fixing it during translation.
- Respect the size limit after translation. If a translated ADR still exceeds the limit, record that for a follow-up rather than restructuring the ADR in this issue.

## Target Files or Areas
- `docs/10_adr/ADR-001-workflow-engine-mandatory.md` through `docs/10_adr/ADR-010-rag-fallback.md`
- `docs/10_adr/ADR-012-git-mcp-server-side-write-enforcement.md`, `docs/10_adr/ADR-013-eventbus-authentication-authorization.md`, `docs/10_adr/ADR-014-agent-control-plane-responsibility-boundaries.md`, `docs/10_adr/ADR-015-reference-document-class-disposition.md`
- `docs/10_adr/adr-index.md`

## Required Changes
- Translate the Japanese prose, titles, and front matter in each listed file into English.
- Update `adr-index.md` titles to match.
- Report each translated ADR's size against the `check_docs_structure.py` limit.

## Constraints
- Do not change meaning. Preserve identifiers, invariant IDs, status values, dates, and quoted code exactly.
- Follow `docs/00_governance/governance_02_documentation-metadata.md` terminology rules (American English spelling, preferred terms).
- Some ADR checkers (`tools/check_adr_structure.py`, `tools/check_adr_reference.py`, `tools/check_adr_invariant_matrix.py`) may parse section headers or markers. Confirm that they still pass after translation.
- A Japanese phrase that is quoted intentionally as an exact string to match may stay if it is justified (see `langdoc001` Unresolved Questions).

## Acceptance Criteria
- `uv run python tools/check_docs_japanese.py` no longer lists any `docs/10_adr/` file, or each remaining occurrence has a recorded justification.
- Reviewers confirm semantic fidelity for each translated ADR. The PR description lists each ADR as reviewed.
- All ADR checkers pass with no new findings.
- `adr-index.md` titles match the ADR H1 titles.

## Testing Expectations
Documentation only. Run:
- `uv run python tools/check_docs_japanese.py`
- `uv run python tools/check_adr_structure.py`, `uv run python tools/check_adr_reference.py`, `uv run python tools/check_adr_invariant_matrix.py` (confirm each CLI first)
- `uv run python tools/check_docs_structure.py "docs/10_adr/*.md"` and `uv run python tools/check_docs_quality.py`

## Documentation Impact
Yes. Language change for all ADRs. Decisions stay the same.

## Out of Scope
- Changing any decision, invariant, or status.
- Splitting or restructuring oversized ADRs.
- Japanese text outside `docs/10_adr/` (issue `langdoc001`).

## Dependencies
- `langdoc001` depends on this issue for the English ADR titles used in area-guide link descriptions.
- The policy question in `langdoc001` (the governance_02 "Bilingual text" rule) should be settled before translation starts, in case it allows any Japanese.

## Unresolved Questions
- Should translation be split into one issue per ADR to keep reviews small? Currently it is one issue to be delivered in small batches.
- Who reviews semantic fidelity? No owner is defined in the repository.

## AI Implementation Instruction
- Translate one ADR at a time and preserve its structure line by line where possible.
- Never change decision content. Stop and report any ambiguity instead of resolving it.
- Run the ADR checkers after each ADR.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261001-104551
- **Related target files**: docs/10_adr/ADR-001-workflow-engine-mandatory.md, docs/10_adr/ADR-002-config-isolation.md, docs/10_adr/ADR-003-runtime-tool-registry-routing-authority.md, docs/10_adr/ADR-004-environment-failure-handling-policy.md, docs/10_adr/ADR-005-rag-source-derived-index-relationships.md, docs/10_adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md, docs/10_adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md, docs/10_adr/ADR-008-sqlite-4db-separation.md, docs/10_adr/ADR-009-rag-ft5-text-separation.md, docs/10_adr/ADR-010-rag-fallback.md, docs/10_adr/ADR-012-git-mcp-server-side-write-enforcement.md, docs/10_adr/ADR-013-eventbus-authentication-authorization.md, docs/10_adr/ADR-014-agent-control-plane-responsibility-boundaries.md, docs/10_adr/ADR-015-reference-document-class-disposition.md, docs/10_adr/adr-index.md
