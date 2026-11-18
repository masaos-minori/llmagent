## Goal
Record a safety-tier gap as FATAL (`REQ-002`, ADR-004 INV-07), state the drift behavior accurately (`REQ-001`), and record a FATAL `rag_consistency` entry when the result is inconsistent but carries no finding (`REQ-004`).

## Scope
**Release unit**: N/A: not part of a release unit
- In scope: `StartupValidationPipeline.check_config` (drift comment, safety-tier call site) and `StartupValidationPipeline.check_services` (RAG routing).
- Companion test files: `tests/agent/test_startup_severity_classification.py`, `tests/agent/test_startup.py`.

## Assumptions
- `check_routing_drift(ctx, strict=True)` raises `RuntimeError` on any drift, so the `add_warning` loop at the drift call site never records anything in strict mode (checked in Step 3a). The loop stays: the two companion files pin the call-site mapping with a mocked non-empty return, so only the comment changes.
- After procedure 02 every rule has a builder, so the fallback entry is a fail-closed guard for a future rule without one.
- `check_services` has radon complexity C (19), so the RAG routing moves into a helper instead of growing the method.

## Design decisions
- Safety-tier messages go to `pipeline.add_fatal("routing_safety_tiers", msg, remediation=...)`; `check_routing_safety_tiers` keeps returning a list.
- The loop over `rag_check.findings` and the new guard move into `_record_rag_findings` (new), called from the `else` branch of the `is_consistent` check.

## Alternatives considered
- Raising from `check_routing_safety_tiers`: rejected; it would change the return contract used by `tests/agent/shared/test_startup_validation_pipeline.py`.
- Removing the drift loop: rejected for the reason in Assumptions.

## Implementation
### Target file
`scripts/agent/startup_validation.py`

### Procedure
1. In `check_config`, replace the drift comment `# Strict-only: a drift finding is always FATAL ...` with: strict mode raises `RuntimeError` on any drift and the handler below records it as FATAL; the returned messages are informational and empty in strict mode.
2. In `check_config`, change the safety-tier loop to `pipeline.add_fatal("routing_safety_tiers", msg, remediation="Declare a safety tier for the tool under [tool_safety_tiers] in config/agent.toml (ADR-004 INV-07).")`; update the comment to say a gap is Fail-Closed per INV-07.
3. Add `_record_rag_findings(pipeline, rag_check)` (new) near the other module-level helpers: it contains the existing per-finding loop (FATAL to `add_fatal`, otherwise `add_warning`) and, when `rag_check.findings` is empty, `pipeline.add_fatal("rag_consistency", ...)` stating that the result is inconsistent with no finding recorded.
4. In `check_services`, replace the `else:` body with a call to `_record_rag_findings` (new).

### Method
- Keep the message format `f"{finding.message} Repair action: {finding.repair_action}"` unchanged.
- The fallback message names the cause ("inconsistent result without a finding") and the effect (RAG consistency cannot be trusted); English, no history wording.

### Details
- `agent.startup_validation` is imported by the startup pipeline and tests only (checked in Step 3a); no import-linter contract is touched.
- Keep every `# noqa` justification as is.

### Companion test files
- `tests/agent/test_startup_severity_classification.py`
  - Procedure: rename `test_routing_safety_tiers_warning_on_messages` to `test_routing_safety_tiers_gap_is_fatal` (new) and assert `StartupCheckStatus.FATAL` for the single outcome; leave the drift tests unchanged.
  - Validation: `uv run pytest tests/agent/test_startup_severity_classification.py`.
- `tests/agent/test_startup.py`
  - Procedure: same rename and FATAL assertion for its `test_routing_safety_tiers_warning_on_messages`.
  - Validation: `uv run pytest tests/agent/test_startup.py`.

## Compatibility considerations
- A configuration with a registered tool missing from `[tool_safety_tiers]` now aborts startup instead of warning (intended, INV-07); a production configuration should be checked read-only before deploy.
- The RAG routing result is unchanged for every case that had a finding.

## Security considerations
- Strengthens the Fail-Closed boundary of ADR-004 INV-07; no setting can downgrade the new FATAL.

## Rollback considerations
N/A: revert the commit; no persisted data is touched.

## Validation plan
- `uv run pytest tests/agent/test_startup_validation.py tests/agent/test_startup_severity_classification.py tests/agent/test_startup.py tests/agent/shared/test_startup_validation_pipeline.py`.
- Validation sequence of `rules/toolchain.md`; diff-cover 100% needs the fallback branch tested (procedure 06).

## Completion criteria
- A safety-tier gap yields a FATAL `routing_safety_tiers` entry; the drift comment matches the code; an inconsistent result without findings yields a FATAL `rag_consistency` entry; the two companion tests assert FATAL.

## Out of Scope
- `scripts/agent/services/routing_drift.py` (procedure 05), new tests for the fallback and real drift (procedure 06), the empty `tool_safety_tiers` behavior (UNK-03).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit `check_config` and `check_services`, add `_record_rag_findings` (new) (Implementation > Procedure) | Completed | 20261118-140956 | 20261118-140956 | Changed: scripts/agent/startup_validation.py, tests/agent/test_startup_severity_classification.py, tests/agent/test_startup.py. Companion tests expect exc is not None because the orchestrator raises on FATAL. |
| 2 | Update the two companion tests (Companion test files) | Completed | 20261118-140956 | 20261118-140956 | — |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261118-140956 | 20261118-140956 | — |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-002, REQ-004
- **Source issue**: issues/20261117-123005_adrchk005_startup-fail-closed.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261118-134945_adrchk005_startup-fail-closed.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-135645
- **Related target files**: `scripts/agent/startup_validation.py`, `tests/agent/test_startup_severity_classification.py`, `tests/agent/test_startup.py`
