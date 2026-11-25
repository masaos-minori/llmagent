# Register the missing ADR-013 invariants in the coverage index and manifest

## Priority
Medium

## Summary
The ADR-013 body cites automated tests for INV-01 to INV-07, but the ADR index matrix and the invariant coverage manifest register only INV-02 and INV-07, and two verification rows in the ADR body carry the wrong invariant id.

## Background
Verified against master on 2026-11-25 (source: local note `memo-issue.md`, issues 012 and 019):
- Confirmed: `docs/10_adr/adr_01_index.md:228` and `registry/manifests/invariant_coverage.yaml` (one `adr: ADR-013` entry, invariants `INV-02, INV-07`) cover only those two; `INV-01`, `INV-03`, `INV-04`, `INV-05`, and `INV-06` have no row.
- Confirmed: the ADR body's Automated Tests table already names concrete tests for them (for example `test_load_config_rejects_unknown_key` for INV-04, `test_no_credential_leakage_in_audit_records` for INV-05, `test_non_loopback_host_raises_value_error` for INV-06).
- New finding: two rows of that table ("One-generation publish" and "Failed rebuild preserves previous generation's principals") are labeled `INV-01`, but INV-01 is "All EventBus routes MUST reject unauthenticated requests with HTTP 401" (`adr_02_04_013_eventbus-authentication-authorization.md:207`); the rows verify the one-generation publication decision, not INV-01.
- Refuted: the note says the Admin route sentence is concatenated with the non-superset role statement. In the source they are separate lines (`:75-77`), and `registry/manifests/eventbus_route_roles.yaml` maps `/admin/topics/authorization` to the admin role alone.
- Gates are currently green: `check_adr_invariant_matrix.py` reports no issues, and `.github/run_cited_adr_tests.py` runs in CI (`ci.yml:57`).

## Problem
Coverage for five of seven ADR-013 invariants is invisible to the matrix checker and the cited-test CI gate, and two evidence rows point at the wrong invariant.

## Reason for Change
Unregistered invariants are not protected against test deletion by the cited-test gate.

## Implementation Intent
Register the missing invariants with concrete test nodes, correct the mislabeled rows, and add the TTL-precedence and publication evidence only after issues/20261125-103307_adrr001_admin-ttl-precedence.md and issues/20261125-103308_adrr002_authz-publication-invariant.md fix their test names. Update canonical sources first and regenerate manifests with the repository tools.

## Target Files or Areas
- `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`
- `docs/10_adr/adr_01_index.md`
- `registry/manifests/invariant_coverage.yaml`

## Required Changes
- Add rows for ADR-013 INV-01 and INV-03 to INV-06 with accurate status and gate values and concrete test nodes.
- Relabel the two one-generation rows to the decision they verify, or to a correct invariant.
- Regenerate the manifest through the existing generator; do not hand-edit generated output.

## Constraints
- Evidence must name existing test nodes; no generic `Confirmed` text.
- Do not change any ADR decision.

## Acceptance Criteria
- ADR-013 INV-01 to INV-07 are each represented in the index and the manifest.
- Every automated evidence entry resolves to an existing test node; `check_adr_structure.py`, `check_adr_invariant_matrix.py`, reference generation, and the cited-test gate pass.

## Testing Expectations
Run every cited ADR-013 test node, the ADR checkers, `uv run python tools/generate_reference_table.py --check`, and `uv run python .github/run_cited_adr_tests.py`.

## Documentation Impact
The ADR body, the ADR index, and the generated manifest change; no decision text changes.

## Out of Scope
- Admin route behavior (issues/20261125-103307_adrr001_admin-ttl-precedence.md, issues/20261125-103308_adrr002_authz-publication-invariant.md).

## Dependencies
- Depends on issues/20261125-103307_adrr001_admin-ttl-precedence.md and issues/20261125-103308_adrr002_authz-publication-invariant.md for the TTL-precedence and publication test names.

## Unresolved Questions
- `不明`: which invariant, if any, the one-generation tests should be registered under (a new invariant needs a maintainer decision).

## AI Implementation Instruction
Register only evidence that exists; do not add approval text; regenerate generated files with the repository tools.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261125-103309
- **Related target files**: `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`, `docs/10_adr/adr_01_index.md`, `registry/manifests/invariant_coverage.yaml`
