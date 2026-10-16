# Extend ADR-004 failure policy verification coverage

## Priority
Low

## Summary
Give each ADR-004 failure class automated evidence, or a stated reason for manual review, so the cross-cutting Fail-Fast and Fail-Closed guarantees are not carried by partial tests and manual audit alone, and keep the ADR and the ADR Index status in line with the evidence.

## Background
Source: finding V24-05 in `memo1.md`, the design document review of 2026-10-16. The ADR documents themselves state the gaps accurately, so this is a verification gap and not a documentation contradiction. Verified against the repository on 2026-10-16:
- `docs/10_adr/adr_02_004_environment-failure-handling-policy.md` Automated Tests table: the row for INV-06 and INV-07 (initialization failure of the RuntimeToolRegistry, a required DB connection, and failures of authentication, authorization, Allowlist, Safety Tier, Config Isolation, or approval-control establishment) is `Partial`; INV-10 (safety or integrity failures not converted to partial availability) is `Partial (see adr_01_index.md)`; INV-15 and INV-16 (Fallback only per ADR-010) is `Not verified (manual audit only)`.
- `docs/10_adr/adr_01_index.md`, ADR Invariant Verification Matrix: the row for ADR-004 INV-07 and INV-10 is `Partial`, with the safety-tier, strict-key, and `allowed_tools` checks covered in `tests/agent/test_production_config_validator.py` and no test for authentication, secrets, Config Isolation, approval-control establishment, or duplicate tool ownership as one cross-cutting guarantee; the row for INV-15 and INV-16 is `Not verified` with only ADR-010 marker uniqueness automated in `tests/rag/test_rag_pipeline_service.py::TestFallbackMarkerLockGuard`.
- The ADR's Manual Review section also records that no test directly verifies INV-01, and INV-02 and INV-13 have no dedicated entry.

Plan-phase findings on 2026-10-16: (1) The active Frozen plan `plans/20261015-112526_plan.md` (issue audit001, moving MCP security validation to per-server self-validation) lists `docs/10_adr/adr_02_004_environment-failure-handling-policy.md` (REQ-020) and `docs/10_adr/adr_01_index.md` (REQ-018) as modification targets, and plans targeting the same files cannot be frozen together; it also rewrites ADR-004's posture-failure classification, which this issue's matrix depends on. A plan for this issue is therefore deferred until audit001 is implemented, and the failure-class mapping must be re-verified against the ADR-004 text at that time. (2) Existing tests already cover more failure classes than the `Partial` status suggests, for example `tests/agent/test_startup_severity_classification.py` (security audit fatal, MCP authentication fatal when a server has no token, readiness fatal in production mode, tool discovery fatal in strict mode, routing drift fatal), `tests/agent/test_production_config_validator.py`, `tests/shared/test_config_loader.py` (Config Isolation), and `tests/shared/test_tool_registry.py` (duplicate ownership); the matrix work starts from these, and the decisions already taken with the requester are: a new cross-cutting test module plus the ADR and ADR Index updates, and the manual fallback audit is kept with its rationale recorded.

## Problem
- The central guarantees of ADR-004 (safety and integrity failures are Fail-Fast at startup or Fail-Closed at runtime and are never downgraded to partial availability; Fallback exists only where an Accepted ADR defines it) are not proved for every listed failure class.
- The Fallback audit is a manual release-review procedure, so a new, undeclared fallback would not be caught by CI.
- Startup Fail-Fast and runtime Fail-Closed behavior are listed together in one `Partial` row, so a gap in one cannot be seen apart from the other.

## Reason for Change
The ADR is Accepted and other ADRs depend on it. Its main guarantees should have evidence a gate can check, or an explicit and reasoned manual-review basis, so the status shown in the ADR and the ADR Index matches what is actually verified.

## Implementation Intent
- Build a Verification matrix by failure class (authentication, authorization, Allowlist, Safety Tier, secrets, Config Isolation, approval-control establishment, RuntimeToolRegistry initialization, duplicate tool ownership, required DB connection) that separates the startup Fail-Fast check from the runtime Fail-Closed check, and records the evidence for each.
- Fill the cheapest automatable gaps with tests; for the fallback audit, evaluate a registry of permitted fallbacks (or an equivalent cross-cutting check) and record the decision.
- Update the ADR and ADR Index statuses to match, without altering any ADR Decision or Invariant.

## Target Files or Areas
- `docs/10_adr/adr_02_004_environment-failure-handling-policy.md` (Automated Tests and Manual Review sections)
- `docs/10_adr/adr_01_index.md` (ADR Invariant Verification Matrix rows for ADR-004)
- `tests/` for the failure classes that gain automated evidence (candidate: near `tests/agent/test_production_config_validator.py`; exact files Unknown until each class is mapped to its startup code)
- A fallback-audit check under `tools/` or `tests/`, only if the registry approach is adopted (Unknown)

## Required Changes
- Create the failure-class by phase matrix and record, for each cell, the existing test, a new test, or the reason it stays manual.
- Add tests for the failure classes that can be verified without changing production code; for each class record whether startup aborts (Fail-Fast) and whether the runtime path rejects (Fail-Closed).
- Add a check that safety or integrity failures are not turned into partial availability, covering the classes in the matrix, or document why a class cannot be checked automatically.
- Decide on a registry or check for permitted fallbacks and record the decision; implement it only if its scope is bounded.
- Update the statuses in the ADR and the ADR Index to the evidence found, then run the ADR and docs checkers.

## Constraints
- Do not change an ADR Decision or Invariant; status and evidence text only (`tools/check_adr_preservation.py`).
- Tests must not open production DBs and must not change production behavior.
- `docs/` is written in English; follow `skills/DESIGN.md` Docs content policy.

## Acceptance Criteria
- Every ADR-004 failure class has either an automated test reference or an explicit manual-review reason in the matrix, split by startup Fail-Fast and runtime Fail-Closed.
- A test or documented check shows that safety and integrity failures are not converted to partial availability for the classes in the matrix.
- The fallback audit has either an automated check or a recorded decision not to automate it, with the reason.
- The status columns in ADR-004 and `adr_01_index.md` match the recorded evidence, and `tools/check_adr_preservation.py` reports no ERROR.
- The new tests pass in the full suite.

## Testing Expectations
- Unit and integration tests for the failure classes added; run the full suite once.
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_adr_preservation.py`, and the ADR matrix checkers named in `routing.md`.

## Documentation Impact
Yes: the Automated Tests and Manual Review parts of ADR-004 and the ADR-004 rows of the ADR Invariant Verification Matrix; verification status and failure behavior, with no change to Decisions.

## Out of Scope
- Changing how ADR-004 classifies failures or its Decisions, redesigning startup validation, and the Fallback policy of ADR-010.
- High-risk MCP protection layers (a separate finding) and the Deployment DB inventory.

## Dependencies
- No open issue under `issues/` covers this (only `20261014-155503_mem001_implement-memory-command-spec.md` is open and it does not touch ADR-004).
- Related to the ADR-010 fallback marker guard test, which is the one automated fallback check that exists.
- Blocked by the implementation of `plans/20261015-112526_plan.md` (audit001): both change `docs/10_adr/adr_02_004_environment-failure-handling-policy.md` and `docs/10_adr/adr_01_index.md`; create this issue's plan after that plan lands.

## Unresolved Questions
- Which startup code paths and tests correspond to each failure class (for example authentication and secrets); not mapped in this review.
- Whether a registry of permitted fallbacks is worth its upkeep compared with the existing manual release review; not decided.
- Whether INV-01, INV-02, and INV-13 should also gain tests or stay manual; recorded in the ADR as manual and not examined here.

## AI Implementation Instruction
Map each failure class to its code and tests before writing any status; claim an evidence level only when a test or command output shows it. Change only status and evidence text in the ADR documents, keep Decisions and Invariants unchanged, add tests without touching production code, and stop and ask if a class cannot be tested without a production change.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261016-125807
- **Related target files**: docs/10_adr/adr_02_004_environment-failure-handling-policy.md, docs/10_adr/adr_01_index.md, tests/agent/test_production_config_validator.py
