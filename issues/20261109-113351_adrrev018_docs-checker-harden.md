# Harden the documentation checkers so the contradictions found in the ADR review cannot recur

## Priority
Medium

## Summary
Close the checker gaps that let the ADR review's defect classes through: a class/function inventory table that `check_docs_content_policy.py` does not flag, free-text contradictions outside the claim registry, history wording and plan IDs, and a Known Deviation sync check that ran against an empty ledger. Add regression tests that re-introduce each defect and assert failure.

## Background
- Source: `memo-issue.md` items H-16 (checker part), M-11 (forbidden-pattern part), and L-02, re-checked against current source on 2026-11-09.
- `Operationally observed`: `uv run python tools/check_docs_content_policy.py --strict` printed "No issues found." on 2026-11-09 although `docs/24_eventbus/eventbus_08_reference_api.md` contains a `File | Class/Function | Signature | Summary` table. `Explicit in code`: `tools/check_docs_content_policy.py` detects an index table only when the first column header is `Function`, `Method`, or `Class` and a later column is `Signature` or `Description` (`_INDEX_TABLE_HEADER_RE`), so a table whose first column is `File` and whose last column is `Summary` is outside the pattern. `Needs confirmation`: whether an exemption (for example generated blocks) also applies; the cause is most likely the pattern gap.
- `Explicit in documentation`: `governance_04` lists GV-018 (docs content policy) as a Blocking check.
- `Explicit in config`: `config/documentation_canonical_sources.toml` registers claim types such as `runtime-behavior`, `database-schema`, `documentation-metadata`, and `operational-procedure`. `Needs confirmation`: the claim types the memo asks for (posture-failure handling, empty-token handling, the DLQ threshold operator, offset monotonicity) are not present (only four types were listed by a partial search).
- `Needs confirmation`: the Known Deviation sync (`tools/check_known_deviation_sync.py`) behavior against an empty ledger, and the forbidden-pattern list location (candidates: `config/doc_quality_rules.json` and `tools/check_docs_*.py`); history phrasings such as "Amendment ... superseded", "replaces the previous", "removed in version N", and plan IDs reportedly pass (several such phrasings exist in current documents; see the history wording issue in this batch).
- Related archived issues under `issues/done/`: `gov008` to `gov017`, `identmatch_*`, `compressverify_*`, `anchorcheck_*` (checker automation work). Re-verify this issue against them before planning; some of the requested checks may exist.

## Problem
- A Blocking rule that a document passes untouched means either an undocumented exemption or a pattern gap; both make the rule unreliable.
- Free-text contradictions are invisible to a cross-document check that compares only registered claims, so the same classes of defect can return after the other fixes in this batch.
- History wording and plan IDs pass the forbidden-pattern checks.

## Reason for Change
- Manual review does not scale; each major finding of the ADR review was a contradiction that tooling could in principle detect. Timing: after the corpus is cleaned by the history wording issue, so the new rules start green.

## Implementation Intent
- Each class of defect found in the ADR review is caught automatically in CI. Extend existing checkers and registries; do not write parallel tools.

## Target Files or Areas
- `tools/check_docs_content_policy.py`, the forbidden-pattern source (`config/doc_quality_rules.json` or `tools/check_docs_*.py`; `Unknown` until confirmed), `tools/check_canonical_source_conflicts.py`, `tools/check_canonical_source_registry.py`, `tools/check_known_deviation_sync.py`, `config/documentation_canonical_sources.toml`
- `tools/TOOL_DESCRIPTIONS.md`, `.pre-commit-config.yaml`, `.github/workflows/ci.yml` (only if a check's wiring changes)
- Tests for the tools (`tests/tools/` or the existing location; `Unknown`)
- `docs/00_governance/governance_04_documentation-checks.md`

## Required Changes
- Find why the checker missed the `eventbus_08` table (exemption or pattern gap), fix it, and add a fixture with that table shape (first column `File`, last column `Summary`).
- Add claim types for posture-failure handling, empty-token handling, the DLQ threshold operator, and offset monotonicity, and register the normative source of each in `config/documentation_canonical_sources.toml` (after the owning ADRs are settled by the other issues in this batch).
- Extend the forbidden-pattern list with history phrasings and plan-ID patterns.
- Add checker tests that re-introduce each resolved contradiction (and an inventory table, and history wording) and assert failure.
- Confirm the Known Deviation sync check fails when an ADR Known Deviations entry has no ledger counterpart, and add a test if it does not.

## Constraints
- Follow `rules/coding.md` and the `routing.md` "Adding a new tool" validation for any `tools/*.py` change; update `tools/TOOL_DESCRIPTIONS.md` in the same change (`check_tool_descriptions_sync.py`).
- Respect module size gates (`check_module_size.py --scripts-dir tools`).
- New rules must not fail on the current corpus except for documents named by other issues in this batch (otherwise land them after those issues merge).
- Registry changes must pass `check_canonical_source_registry.py` (single normative source per claim type).

## Acceptance Criteria
- Re-introducing any resolved contradiction, an inventory table of the `eventbus_08` shape, or history wording fails the checker (and CI).
- The checkers pass on the current corpus.
- `uv run python tools/check_docs_content_policy.py --strict`, `check_canonical_source_registry.py`, `check_known_deviation_sync.py`, `check_tool_descriptions_sync.py`, and the tool module size checks pass; ruff, mypy, and bandit pass for the changed tools.

## Testing Expectations
- Unit tests for each checker change with fixtures for the defect shapes; one regression test per resolved contradiction class; run `uv run pytest` for the tool tests and the standard validation sequence from `rules/toolchain.md` for `tools/`.
- A smoke run of each changed checker against real `docs/` content.

## Documentation Impact
- `governance_04` and `tools/TOOL_DESCRIPTIONS.md` describe the new or extended checks: intent, scope, and failure behavior. Update the registry documentation if claim types change.

## Out of Scope
- Fixing the documents the checkers flag (other issues in this batch).
- Changing the ADR content or governance rules themselves.

## Dependencies
- Depends on: `issues/20261109-113318_adrrev017_docs-history-wording.md` (clean the corpus first so new rules start green).
- Related: `issues/20261109-112504_adrrev001_eventbus-route-handlers.md` (rewrites `eventbus_08`; the new fixture must not depend on the old table being present).
- Related, recently archived: `gov008` to `gov017` and `identmatch_*` under `issues/done/`.

## Unresolved Questions
- `Needs confirmation`: whether the `eventbus_08` miss is an exemption or a pattern gap, and where the forbidden-pattern list lives.
- `Needs confirmation`: which of the requested claim types and patterns already exist.
- Maintainer decision: severity (Blocking versus Warning) of the new forbidden patterns.

## AI Implementation Instruction
- Reproduce the miss first and extend the existing checker; do not add a second checker.
- Do not edit documents to make a new check pass; report them for the owning issue.
- Follow the tool validation sequence and keep `tools/TOOL_DESCRIPTIONS.md` in sync.
- Write messages and comments in English; do not commit.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261109-113351
- **Related target files**: `tools/check_docs_content_policy.py`, `tools/check_canonical_source_conflicts.py`, `tools/check_canonical_source_registry.py`, `tools/check_known_deviation_sync.py`, `config/documentation_canonical_sources.toml`, `config/doc_quality_rules.json`, `tools/TOOL_DESCRIPTIONS.md`, `docs/00_governance/governance_04_documentation-checks.md`
