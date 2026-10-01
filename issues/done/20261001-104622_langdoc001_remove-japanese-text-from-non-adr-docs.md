# Remove Japanese text from non-ADR docs and reconcile the bilingual-text rule

## Priority
Medium

## Summary
Besides the ADRs, 13 files under `docs/` contain Japanese text. That violates the `skills/DESIGN.md` rule that every file under `docs/` is English, with no exception. Most occurrences are Japanese ADR titles copied into link descriptions. The rest are Japanese prose, Japanese quotes of ADR boilerplate, Japanese marker words that a checker needs, and a full-width punctuation character. Classify each occurrence, then translate or justify it. Also reconcile the `docs/00_governance/governance_02_documentation-metadata.md` "Bilingual text" rule, which appears to allow Japanese alternatives, with the English-only rule.

## Background
- `skills/DESIGN.md` Output language: all files under `docs/` are English, with no exception. `Documentation only`
- `docs/00_governance/governance_02_documentation-metadata.md` Usage Rules item 3: "Bilingual text: Use English preferred form with Japanese alternative in parentheses on first occurrence." `Documentation only`
- `tools/check_docs_japanese.py` lists files that contain Japanese characters. It always exits 0 and has no allowlist. `Explicit in code`

## Problem
Occurrences found on 2026-10-01, grouped by kind:
- Japanese ADR titles copied into link descriptions:
  - `docs/90_deployment/deployment_00_document-guide.md`
  - `docs/40_shared/shared_00_document-guide.md`
  - `docs/91_security/security_00_document-guide.md`
  - `docs/21_rag/rag_00_document-guide.md`
  - `docs/21_rag/rag_91_design_notes.md`
  - `docs/22_mcp/mcp_00_document-guide.md` (Related ADRs)
  - `docs/24_eventbus/eventbus_00_document-guide.md`
  - `docs/23_agent/agent_00_document-guide.md`
- Japanese prose:
  - `docs/23_agent/agent_02_runtime-architecture.md`, `## Preflight Gate Coverage` (two sentences)
  - `docs/10_adr/10_adr_00_document-guide.md`, `## Known Deviations`
- Quotes of Japanese source text:
  - `docs/21_rag/rag_01_system_overview.md` quotes the Assumptions section of ADR-008.
  - `docs/00_governance/governance_01_documentation-policy.md`, `## ADR Section Header Standardization`, quotes three Japanese ADR boilerplate notes, each followed by an English translation.
- Functional Japanese tokens: `docs/00_governance/governance_04_documentation-checks.md` lists the Japanese marker words that a checker matches, such as 解消 and 解決.
- Full-width punctuation: `docs/22_mcp/mcp_00_document-guide.md` uses `〜` as a range separator in its chapter table.

## Reason for Change
- The output-language rule is absolute, but `check_docs_japanese.py` cannot tell intended exceptions from violations, so it cannot serve as a pass/fail gate.
- The governance_02 bilingual rule and the DESIGN.md rule contradict each other, and readers cannot tell which one wins.

## Implementation Intent
- First decide the meaning of the governance_02 "Bilingual text" rule. Either it is obsolete and must be reworded or removed, or it allows a narrow exception that `skills/DESIGN.md` must state. Use the documentation-policy precedence to decide which rule is canonical, and do not guess.
- Then classify each occurrence:
  - Translate link descriptions and prose into English. Use the English ADR titles that `langadr001` produces.
  - For quotes of Japanese source text, replace them with English once the source ADRs are translated (`langadr001`). Until then, keep them, with the dependency recorded.
  - Keep functional tokens that a checker must match only if the language rule allows them. In that case, justify them, and optionally add a narrow allowlist to `check_docs_japanese.py`.
  - Replace full-width punctuation with ASCII equivalents.

## Target Files or Areas
- `docs/00_governance/governance_02_documentation-metadata.md` (Usage Rules item 3)
- `skills/DESIGN.md` (Output language), only if a narrow exception is approved
- The 13 non-ADR files listed in Problem
- `tools/check_docs_japanese.py`, only if an allowlist is approved

## Required Changes
- Resolve the governance_02 versus DESIGN.md contradiction, and record the decision in the canonical location.
- Translate the Japanese link descriptions and prose.
- Replace the Japanese quotes after `langadr001`, or record why they stay.
- Replace `〜` with an ASCII equivalent.
- Decide how to handle the Japanese checker marker words in governance_04.

## Constraints
- Do not change meaning. Translate the identifiers in link targets and code only if they are themselves Japanese (none expected).
- Follow governance_02 terminology rules (American English).
- Modified `tools/*.py` must pass the `routing.md` "Adding a new tool" validation sequence.

## Acceptance Criteria
- `uv run python tools/check_docs_japanese.py` lists none of the 13 files, or every remaining occurrence has a recorded, rule-backed justification.
- The governance_02 "Bilingual text" rule and `skills/DESIGN.md` Output language no longer contradict each other.
- Area-guide ADR link descriptions match the English ADR titles.

## Testing Expectations
Mainly documentation. Run:
- `uv run python tools/check_docs_japanese.py`
- `uv run python tools/check_docs_structure.py` on the edited files, and `uv run python tools/check_docs_quality.py`
- `uv run python tools/check_skills_references.py`, if `skills/DESIGN.md` is edited
- `uv run pytest tests/tools`, if `check_docs_japanese.py` is changed

## Documentation Impact
Yes. Language and terminology rules, plus English wording in area guides and governance docs.

## Out of Scope
- ADR bodies and `adr-index.md` (issue `langadr001`).
- Any other content change in the listed files.

## Dependencies
- Depends on `langadr001` for the English ADR titles and the translated ADR boilerplate.
- `langadr001` should wait for this issue's policy decision on the bilingual rule.
- Edits `agent_00_document-guide.md`, which `ncagent001` and `docleft001` also touch. Coordinate the order.

## Unresolved Questions
- Is the governance_02 "Bilingual text" rule obsolete, or an intended exception?
- May checker-required Japanese marker words remain in governance_04?

## AI Implementation Instruction
- Get the policy decision before translating anything, and stop and ask if it is unclear.
- Classify every occurrence in a table in the plan or PR before you edit.
- Do not translate quoted ADR text ahead of `langadr001`.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261001-104622
- **Related target files**: docs/00_governance/governance_02_documentation-metadata.md, skills/DESIGN.md, docs/90_deployment/deployment_00_document-guide.md, docs/40_shared/shared_00_document-guide.md, docs/91_security/security_00_document-guide.md, docs/21_rag/rag_00_document-guide.md, docs/21_rag/rag_01_system_overview.md, docs/21_rag/rag_91_design_notes.md, docs/22_mcp/mcp_00_document-guide.md, docs/10_adr/10_adr_00_document-guide.md, docs/00_governance/governance_01_documentation-policy.md, docs/00_governance/governance_04_documentation-checks.md, docs/24_eventbus/eventbus_00_document-guide.md, docs/23_agent/agent_00_document-guide.md, docs/23_agent/agent_02_runtime-architecture.md, tools/check_docs_japanese.py
