# Decide consistency check coverage for the eventbus and shared db docs domains

## Priority
Low

## Summary
`tools/check_docs_consistency.py` has no domain for the EventBus and Shared/DB documents, so the docs cleanup could not run it for them. Decide whether to add coverage, and apply the decision.

## Background
`memo4.md` ("Unexecuted checks") lists `check_docs_consistency.py` for eventbus and db as not run because the domain does not exist. `governance_04_documentation-checks.md` states that `--domain` accepts only five domains (agent, mcp, rag, deployment, overview) and that EventBus and Shared/DB documents are not covered. `docs/` contains `24_eventbus/`, `40_shared/`, and `41_db/`. `governance_05` lists EventBus and Shared/DB among the five in-scope nodes of the change-impact graph. The tool maps each domain to a docs subfolder (`DOMAIN_SUBFOLDERS`) and a set of generic checks.

## Problem
Doc claims in `24_eventbus/`, `40_shared/`, and `41_db/` (links, `scripts/` path references, function references, config keys, DB claims) are not cross-checked against code and config by this tool. Whether the gap is deliberate is unknown; `governance_04` records it as a fact, not as a decision.

## Reason for Change
These documents carry ownership and DB-boundary claims. Without an automated cross-check, stale references can go unnoticed, and the docs cleanup verification had to leave them unrun.

## Implementation Intent
Decide first, based on measurement. Run the generic checks (link, path, function reference) against the three folders by adding a domain or reusing the generic set, and record the findings on live data. Add only checks that apply (generic ones by default); do not invent domain-specific drift checks without a concrete claim to verify. If the owner prefers not to cover them, record that as a design decision in `governance_04`.

## Target Files or Areas
- `tools/check_docs_consistency.py` (`DOMAIN_SUBFOLDERS`, `DOMAIN_PREFIXES`, generic check mapping)
- `tests/tools/` (tests for the tool, if present; otherwise Unknown)
- `docs/00_governance/governance_04_documentation-checks.md`
- `tools/TOOL_DESCRIPTIONS.md`, `rules/toolchain.md`, `routing.md` (descriptions of domains, if changed)

## Required Changes
- Run the generic checks against `24_eventbus/`, `40_shared/`, and `41_db/` as a dry measurement and record the findings.
- Record the owner's decision: add domains, or keep the five domains by design.
- If adding: register the domains and their generic check set; triage the findings on live docs (fix, or file follow-ups).
- Update `governance_04` (the statement of covered domains, and the matrix if a rule is added) and the tool description.

## Constraints
- New checks start at Warning and must not fail on the existing corpus.
- Follow `routing.md` "Adding a new tool" validation for tool changes.
- Do not change the existing five domains' behavior or GV-023.

## Acceptance Criteria
- The coverage decision for EventBus and Shared/DB docs is recorded in `governance_04`.
- If domains are added: the tool runs on them without error, findings are triaged, and the docs and tool descriptions state the new domains.
- Existing domain runs produce the same results as before.

## Testing Expectations
- Unit tests for the new domain mapping (fixture docs with a valid and a stale reference).
- `uv run python tools/check_docs_consistency.py --domain <each domain>` on live docs.
- `uv run ruff`, `uv run mypy tools/check_docs_consistency.py`, `uv run bandit tools/check_docs_consistency.py`.
- `uv run python tools/check_tool_descriptions_sync.py`, `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py` for edited docs.

## Documentation Impact
Yes. `governance_04` (covered domains, matrix if changed), `tools/TOOL_DESCRIPTIONS.md`, and `rules/toolchain.md` if the domain list changes.

## Out of Scope
- Domain-specific drift checks without a concrete claim to verify.
- Fixing every finding in `24_eventbus/`, `40_shared/`, `41_db/`.
- Anchor validation (separate issue) and the compression-verification gaps.

## Dependencies
Related open issue in the same batch: `identmatch` (extends `check_docs_consistency.py` identifier matching). Both edit the same tool; coordinate order. Sibling-issue check: `compat001` and `compat002` do not touch these files.

## Unresolved Questions
- Is the absence of these domains deliberate, or an unfinished part of the tool?
- Which generic checks apply to eventbus and shared/db docs?

## AI Implementation Instruction
Measure on live docs before changing the tool. Extend the existing tool; do not add a parallel script. Keep new findings at Warning and do not edit docs content other than the governance and tool descriptions.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261021-101756
- **Related target files**: `tools/check_docs_consistency.py`, `docs/00_governance/governance_04_documentation-checks.md`, `tools/TOOL_DESCRIPTIONS.md`, `rules/toolchain.md`, `routing.md`
