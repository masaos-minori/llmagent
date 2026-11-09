# Fix the ADR index verification matrix, invariant-to-test mappings, and manifest status

## Priority
Medium

## Summary
Make the ADR index and the ADR bodies agree exactly: correct stale manifest status in ADR-015, text errors in ADR-006 and ADR-014, index wording, and the invariant-to-test mappings, so that every Blocking invariant is verified by a real test and every cited test verifies the invariant it claims.

## Background
- Source: `memo-issue.md` items M-05 and M-06, re-checked against current source on 2026-11-09. Several memo claims are confirmed, several stale or unverified.
- `Explicit in documentation`: ADR-015 (`docs/10_adr/adr_02_07_015_docs-reference-document-class-disposition.md`) still says the manifests `component_mandatoriness`, `adr_authority`, and `architecture_assumptions` are deferred "until their source modules land"; `scripts/shared/component_mandatoriness.py` and `config/adr_authority.toml` exist, so the status is stale (`Needs confirmation` for `architecture_assumptions`). `agent_08_04_configuration-mcp-approval-obs.md` is referenced as generated from the registry; a search for a `class:` front-matter line in it found none.
- `Explicit in documentation`: ADR-006 INV-13 says an event promotes when every attempting consumer "has exceeded max_retry", while the cited test is named for `>= max_retry` (`tests/eventbus/test_eventbus_dlq_promotion.py::...test_dlq_promotion_when_consumer_delivery_failure_count_gte_max_retry`). The index row for ADR-006 INV-05/INV-09 says offsets are "strictly monotonic", while ADR-006 Decision 11a accepts an ACK with `new_offset <= current_offset` and leaves the offset unchanged (non-decreasing). The requeue result name `already_redelivered` exists in `scripts/eventbus/dlq_repo.py`; the API's HTTP error text differs (`Needs confirmation`).
- `Explicit in documentation`: the index already states that a row with Verification Status "Not verified" is Non-Blocking (index text), which covers the memo's "apply Not verified implies Non-Blocking" task; `Needs confirmation` that no row still combines "Not verified" with "Blocking: Yes" and that ADR-001 INV-02 and ADR-004 INV-11/12 are in the matrix.
- `Explicit in documentation`: ADR-004 INV-14 is verified by `tests/shared/test_mcp_config.py::TestRequiredDefault`; the memo says that test defaults `required` to true and continues, which contradicts the invariant (abort on undefined mandatoriness) (`Needs confirmation` by reading the test). ADR-014's Decision/INV-02 producer wording was not re-read (`Needs confirmation`).
- Tools that enforce the index: `tools/check_adr_invariant_matrix.py`, `tools/check_adr_structure.py`, `tools/generate_adr_authority.py --check`.

## Problem
- The index is supposed to be a faithful projection of the ADR bodies; wrong wording and unsupported test citations break that rule and mislead implementers.
- "Exceeded" versus `>=` changes when an event moves to the DLQ, so a strict reading of the ADR conflicts with the code.
- A test that continues where the invariant requires abort would let a regression pass.
- Stale deferred-manifest status misdescribes the documentation pipeline.

## Reason for Change
- Verification evidence is the basis of the Blocking gates; inaccurate evidence undermines them. Timing: no external deadline; the authority-model issue in this batch depends on a clean index.

## Implementation Intent
- The index and the ADR bodies agree exactly; every Blocking invariant is verified by a real test; every test verifies the invariant it claims.
- Where an ADR body is wrong, correct it through the ADR amendment process rather than editing the index alone (the ADR body is authoritative).

## Target Files or Areas
- `docs/10_adr/adr_01_index.md`, `docs/10_adr/adr_02_07_015_docs-reference-document-class-disposition.md`, `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`, `docs/10_adr/adr_02_02_014_agent-control-plane-responsibility-boundaries.md`, `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`, `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`
- `docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md` (front matter only)
- `tests/shared/test_mcp_config.py`, `tests/eventbus/` (cited tests)

## Required Changes
- Update the ADR-015 manifest status and the generated-document list (add `agent_08_04`), and add `class: Reference` to the `agent_08_04` front matter if the class rule applies.
- Change the ADR-004 INV-14 test (or the code) so that a missing registry entry aborts startup.
- ADR-014: name a single producer in both the Decision and INV-02.
- ADR-006: change INV-13 to `>= max_retry`, fix the test mapping for the invariants the memo lists (INV-04, 07, 12, 14) after verifying each, and align the requeue error name with the API.
- Index: change "strictly monotonic" to "non-decreasing", remove citations of tests that the ADRs do not contain, and fix the row order.
- Add ADR-001 INV-02 and ADR-004 INV-11/12 to the matrix as Blocking, or record why they are not; confirm that no row combines "Not verified" with Blocking.

## Constraints
- ADR amendments need approval records (governance-ledger issue); the implementer must not fabricate approvals.
- `tools/check_adr_preservation.py` guards unintended decision changes: run it and justify each reported change.
- The index graph sections are generated; use `tools/generate_adr_authority.py` instead of hand edits.
- Do not change test behavior except for the INV-14 test (or code) change named above.

## Acceptance Criteria
- The index checks report zero mismatches against the ADR bodies (`check_adr_invariant_matrix.py`, `check_adr_structure.py`, `check_adr_authority.py`, `generate_adr_authority.py --check`).
- A missing mandatoriness entry fails startup in a test.
- ADR-006 INV-13 text and its cited test agree on the comparison operator.
- `check_docs_structure.py` and `check_docs_content_policy.py --strict` pass.

## Testing Expectations
- `uv run pytest tests/shared/test_mcp_config.py tests/eventbus -v` for the changed or cited tests; the ADR checkers listed above; full validation sequence if the code or a test changes.

## Documentation Impact
- ADR-001, ADR-004, ADR-006, ADR-014, ADR-015, the ADR index, and `agent_08_04` front matter change. State intent and verification status; do not copy test code or config values.

## Out of Scope
- Adding new invariants to ADR-013 (EventBus authorization issue in this batch).
- Authority model, reference edges, and ADR format (separate issue in this batch).

## Dependencies
- Depends on: none.
- Blocks: `issues/20261109-113248_adrrev016_adr-authority-format.md` (authority model and ADR format).
- Related: `issues/20261109-113054_adrrev012_adr-approval-ledger.md` (approval records for the amendments made here).

## Unresolved Questions
- `Needs confirmation`: the ADR-004 INV-14 test behavior; ADR-014 producer wording; the exact set of rows still combining "Not verified" with Blocking; the requeue error text in the API.
- Maintainer approval is required for each ADR amendment.

## AI Implementation Instruction
- Read each cited ADR and test before changing the index; do not edit the index to match the memo alone.
- Run `check_adr_preservation.py` and explain every reported decision change.
- Do not write approval records on a maintainer's behalf.
- Write documentation in English and follow the docs content policy; do not commit.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261109-113220
- **Related target files**: `docs/10_adr/adr_01_index.md`, `docs/10_adr/adr_02_07_015_docs-reference-document-class-disposition.md`, `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`, `docs/10_adr/adr_02_02_014_agent-control-plane-responsibility-boundaries.md`, `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`, `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`, `docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md`, `tests/shared/test_mcp_config.py`
