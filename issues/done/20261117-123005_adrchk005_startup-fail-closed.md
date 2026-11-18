# Make startup validation fail-closed and fix ADR-003 wording

## Priority
High

## Summary
Startup validation lets routing drift, safety-tier gaps, and unverifiable RAG results pass without a fatal result, and ADR-003 describes the same checks inconsistently. Fix the code and the ADR wording together.

## Background
Filed from the consolidated ADR review task list `memo-issue.md` (package `ADRCHK2-H05`; merged from ADRCHK-H05, H06, M01, L04 (review findings H2, H3, M17, N45)). The review's claims carry the evidence label `Documentation only` unless this issue marks them otherwise; the implementer MUST re-verify each claim against current source before changing anything.

## Problem
Claims come from the review (`Documentation only` until re-verified).

## Reason for Change
- Drift findings are warnings: the `check_config` comment says a drift finding is always fatal, but each message from `check_routing_drift(strict=True)` and `check_routing_safety_tiers` goes to `add_warning`, and only an exception goes to `add_fatal`. ADR-004 INV-02 says drift is always fatal.
- Unverifiable RAG checks pass silently: in `scripts/db/rag_consistency.py`, `diagnostic_errors`, a failed `read_smoke_test_ok`, and the `fk_unverified`, `embedding_unverified`, and `schema_unverified` flags make `is_consistent` false but produce no finding, and startup iterates only `findings`.
- ADR-003 contradicts itself: Decision #15 says drift warns while Implementation Notes and Verification say startup aborts; the Startup Validation section limits the abort to `required=true` servers while Decision #16 and ADR-004 abort regardless; an unregistered tool is called Fail-Fast although it fails closed at runtime; the static ToolRegistry is called Derived Data although it is not derived from RuntimeToolRegistry.
- Approval records exist only for some Decisions, so Decisions #16 and #17 are in force without one.

## Implementation Intent
- Any routing drift, safety-tier gap, or unverifiable RAG result produces a recorded non-ok startup entry.
- ADR-003 describes this behavior in one way, uses ADR-004 terms, and shows the approval state of every Decision.

## Target Files or Areas
- `scripts/agent/startup_validation.py`
- `scripts/agent/services/routing_drift.py`
- `scripts/db/rag_consistency.py`
- `scripts/db/models.py`
- `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`
- `tests/agent/`
- `tests/db/`

## Required Changes
- Read `routing_drift.py`. If strict mode raises on every finding, document the returned messages as informational and fix the comment; otherwise send them to `add_fatal`. Apply the same rule to `check_routing_safety_tiers`.
- Add issue builders for the silent rules. Use FATAL until the RAG severity decision is recorded.
- In startup validation, add a fatal `rag_consistency` entry when `is_consistent` is false and no finding was recorded.
- In ADR-003, fix the Decision #15 severity, use "regardless of `required`", fix the Fail-Fast and Derived Data terms, and mark Decisions #16 and #17 as pending (pending form from the governance issue).

## Constraints
- Keep the `_CHECKS` single-rule design in `rag_consistency.py`; do not add a second list of conditions.
- Do not write, paraphrase, or simulate a maintainer approval statement. A change to an ADR decision, invariant, Blocking value, or authority edge needs an approval record in the same change (governance_01, governance_05).
- Follow the Current-Specification-Only policy: no migrations, aliases, shims, tolerant fallbacks, or history-style comments such as removed on or formerly.
- Change only the Target Files; if another file must change, stop and report it as a scope amendment.
- Keep code comments, log text, and documentation in English.
- Before editing, re-run the searches named in Acceptance Criteria. Other plans edit the same files; if a defect is already gone, record the evidence and skip that task.
- Do not edit generated files (`registry/manifests/*.yaml`, guarded blocks) by hand; regenerate with `tools/generate_reference_table.py` or `tools/generate_adr_authority.py`.

## Acceptance Criteria
- A test with one unregistered routed tool, and a test with one tool missing from `tool_safety_tiers`, each produce a fatal entry.
- A test with `fk_unverified=True` and all counts zero produces a non-ok `rag_consistency` entry.
- ADR-003 Decision #15, the Implementation Notes, and the Verification section use the same severity.

## Testing Expectations
Unit tests under `tests/agent/` and `tests/db/` for each case above; run the full validation sequence and the ADR checkers. Validation sequence: `rules/toolchain.md`; after any `docs/` edit also the checkers listed in `routing.md` Tools.

## Documentation Impact
Yes. ADR-003: severity, abort scope, terminology, and approval state of each Decision.

## Out of Scope
- Choosing the final RAG severity (separate decision).
- Writing approval text for Decisions #16 and #17.

## Dependencies
- `issues/20261117-123006_adrchk006_rag-failure-policy.md` decides the final RAG severity; FATAL is the interim value.
- `issues/20261117-123011_adrchk011_adr-approval-governance.md` defines the pending-marker format used in ADR-003.

## Unresolved Questions
- `scripts/agent/services/routing_drift.py` and `scripts/db/models.py` were not reviewed; whether strict mode raises or returns findings is unknown.

## AI Implementation Instruction
- Read `routing_drift.py` first and report whether strict mode raises before choosing the fix.
- Do not write approval text.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261117-123005
- **Related target files**: `scripts/agent/startup_validation.py`; `scripts/agent/services/routing_drift.py`; `scripts/db/rag_consistency.py`; `scripts/db/models.py`; `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`; `tests/agent/`; `tests/db/`
