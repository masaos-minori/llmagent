# Generate contract manifests and tighten ADR invariant coverage states in CI

## Priority
Low

## Summary
Extend the ADR invariant matrix with explicit coverage states that treat skipped or xfailed evidence as unverified and require an accountable process for manual-only coverage, and generate machine-readable contract manifests (tool ownership, MCP endpoints, EventBus route-role mapping, DB schema versions, configuration ownership, health contracts, component mandatoriness, ADR authority, architecture assumptions, invariant coverage) that documentation and CI both consume.

## Background
Source: `memo-issue.md` item L-01 (original tasks L-01 and L-03), re-verified against current source on 2026-10-29. Part of the memo's checking scope is already enforced, so this issue covers the remainder.

Already in place (`Explicit in code`):
- The ADR Invariant Verification Matrix in `docs/10_adr/adr_01_index.md` (lines 109 onward) records Type, Timing, Gate (Blocking or Non-Blocking) and a Verification Status with four values: `Confirmed`, `Partial`, `Manual`, `Not verified` (line 105). A `Not verified` row is defined as Non-Blocking, and `Partial` and `Manual` rows must name the unverified scope, the manual review, and an Owner.
- `tools/check_adr_invariant_matrix.py` reports `ERROR` for body-evidence rules and checks that cited test files exist and that each `::` segment of a cited pytest node is a class or function defined in the file (module docstring and `_BODY_RULE_SEVERITY = "ERROR"`); it runs as a pre-commit hook (`.pre-commit-config.yaml:56`). `tools/check_adr_reference.py` also runs as a hook (line 62). This was delivered by `issues/done/20261027-155848_adrgate005_enforce-adr-evidence-checks.md`.
- CI runs the cited tests (`.github/workflows/ci.yml:43`, `.github/run_cited_adr_tests.py`).
- Generated reference blocks exist and are guarded: `tools/generate_reference_table.py --check` guards `AUTO-GENERATED` blocks in documents such as `docs/24_eventbus/eventbus_08_reference_api.md`, `docs/23_agent/agent_13_reference-api-generated.md`, and `docs/22_mcp/mcp_01_tool_ownership_matrix.md` (ADR-015 pattern).

Not in place (`Explicit by absence search`):
- No handling of skipped or xfailed cited tests: the matrix checker and the runner contain no skip or xfail logic (the only match is the phrase "skipping the header row").
- No coverage-state vocabulary with `Static` and `Runtime-observed` evidence kinds, and no review cadence field for `Manual`.
- No machine-readable manifests: generated output is Markdown blocks in documents, not separate manifest files that CI and startup validation can read.

## Problem
Blocking invariants can still lose their real coverage without a failing build: a cited test that is skipped or marked xfail passes the existence and run checks; manual coverage has an owner but no cadence or expected evidence; and the contract lists that documentation, startup validation, and CI need are kept as separate hand-maintained or document-embedded copies rather than one generated source.

## Reason for Change
Priority is Low: the existence and run checks already fail the build for missing and dangling evidence, so the remaining items strengthen guarantees and remove duplicate inventories rather than fix a failing control. It becomes more valuable as the other issues in this batch add ADR-governed contracts. It is not time-sensitive.

## Implementation Intent
Add the missing coverage semantics to the existing matrix and checker instead of replacing them: map the current `Confirmed`, `Partial`, `Manual`, and `Not verified` values onto the memo's states where they overlap, add skipped or xfailed detection for cited nodes, and add cadence and expected-evidence fields for manual coverage. Introduce machine-readable manifests as additional outputs of the existing generator pattern (ADR-015), have the Markdown reference blocks be generated from them, and remove superseded hand-maintained copies only after the migration. Manifests that depend on other issues in this batch (component mandatoriness, ADR authority and assumptions) are delivered when those sources exist.

## Target Files or Areas
- `docs/10_adr/adr_01_index.md`, `docs/10_adr/adr_02_07_015_docs-reference-document-class-disposition.md`
- `tools/check_adr_invariant_matrix.py`, `tools/check_adr_reference.py`, `tools/generate_reference_table.py`
- `.github/run_cited_adr_tests.py`, `.github/workflows/ci.yml`, `.pre-commit-config.yaml`
- New manifest schemas and generated manifest files (locations to be decided) and the reference documents that consume them

## Required Changes
- Define the coverage states and their mapping from the current Verification Status values; add cadence and expected-evidence requirements for manual-only coverage.
- Treat skipped and xfailed cited tests as unverified unless an approved exception exists; keep failing the build when cited nodes or commands do not exist.
- Generate machine-readable manifests for tool ownership, MCP endpoints, EventBus route-role mapping, DB schema and version, configuration ownership, health contracts, and invariant coverage (component mandatoriness, ADR authority, and architecture assumptions when their sources exist).
- Generate the reference-document blocks from the manifests and fail CI when a manifest or guarded block drifts from its source.
- Remove superseded hand-maintained copies after migration.

## Constraints
- Reuse the existing generated-block markers and the `--check` mode; generated blocks must not be hand-edited or treated as normative sources.
- Do not weaken or reclassify any Blocking invariant to pass the new checks; unverified blocking evidence must surface as a failure or an explicit approved exception.
- Docs content policy applies to any document edit (`skills/DESIGN.md`).

## Acceptance Criteria
- Every Blocking invariant has valid, current, non-skipped evidence, or an approved exception recorded in the matrix.
- Missing, dangling, skipped, xfailed, or stale evidence fails CI; manual-only coverage records an owner, procedure, expected evidence, and cadence.
- Documentation and CI consume the same generated manifest data; source changes that require regeneration are detected.
- Generated blocks cannot be treated as hand-maintained normative sources.

## Testing Expectations
- Unit tests for the checker changes (skipped test, xfailed test, missing cadence, state mapping) and for manifest generation (reproducibility and drift detection).
- `uv run python tools/check_adr_invariant_matrix.py`, `uv run python tools/check_adr_reference.py`, `uv run python tools/generate_reference_table.py --check`, and the docs checkers in `routing.md`.

## Documentation Impact
Yes. The ADR index must define the coverage states, the mapping from existing values, and the exception process; ADR-015 must describe the manifest outputs. Document intent and boundaries only (`skills/DESIGN.md` Docs content policy).

## Out of Scope
- The ADR authority and assumption models themselves (`issues/20261029-104504_adrauth001_adr-authority-model.md`) and the mandatoriness registry (`issues/20261029-104502_mcpgate001_mcp-mandatory-construction-contracts.md`); this issue consumes them.
- Running the full test suite on every commit, and re-deciding any invariant.
- Unrelated refactoring or formatting-only changes.

## Dependencies
- Depends on `issues/20261029-104504_adrauth001_adr-authority-model.md` and `issues/20261029-104502_mcpgate001_mcp-mandatory-construction-contracts.md` for the manifests that read their sources; the other manifests and the coverage-state work can proceed first.
- Related, archived: `issues/done/20261027-155848_adrgate005_enforce-adr-evidence-checks.md`; re-verify this issue against it and against the checker's current rules.

## Unresolved Questions
- `Needs confirmation`: whether skipped or xfailed detection belongs in `.github/run_cited_adr_tests.py` (which runs the tests) or in the static matrix checker (which cannot see run results).
- `Needs confirmation`: the manifest format and the directory for generated manifests.
- `Needs confirmation`: how to treat the existing `Partial` rows in the migration to the new states (they name an owner but no cadence).

## AI Implementation Instruction
- Read ADR-015, `tools/check_adr_invariant_matrix.py`, and `tools/generate_reference_table.py` before editing; extend them rather than adding a parallel mechanism.
- Do not reclassify a Blocking invariant to make a check pass; stop and report any invariant whose evidence is genuinely missing.
- Deliver the coverage-state work and each manifest as separate, reviewable steps.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261029-104505
- **Related target files**: `docs/10_adr/adr_01_index.md`, `docs/10_adr/adr_02_07_015_docs-reference-document-class-disposition.md`, `tools/check_adr_invariant_matrix.py`, `tools/check_adr_reference.py`, `tools/generate_reference_table.py`, `.github/run_cited_adr_tests.py`, `.github/workflows/ci.yml`, `.pre-commit-config.yaml`
