# Align deployment and Agent-managed MCP lifecycle documentation

## Priority
Medium

## Summary
Document the Agent-managed MCP process lifecycle (spawn, health probe, restart, cooldown, PID ownership, shutdown suppression), align database path and recovery ownership statements, and decide how invalid lifecycle transitions are handled.

## Background
Source: `memo-issue.md` (Issue C). The memo marks the evidence as incomplete; this pass only confirmed which files exist.

- `Explicit in code`: the lifecycle is implemented across `scripts/agent/http_lifecycle.py` and its helper modules (`http_lifecycle_errors.py`, `http_lifecycle_health_checker.py`, `http_lifecycle_process_terminator.py`, `http_lifecycle_shutdown_coordinator.py`, `http_lifecycle_subprocess_launcher.py`, and others).
- `Explicit in code`: `deploy/` contains shell scripts (`deploy.sh`, `setup_services.sh`, `start_agent.sh`, and others). The memo's `deploy/systemd/` directory does not exist; the actual service-definition location is `Needs confirmation`.
- Related plan: `plans/20261110-233648_adrrev009_adr008-recovery-align.md` covers manual recovery procedures for the workflow and EventBus databases.

## Problem
Operational documents may not describe the behavior implemented in the lifecycle modules, and the handling of invalid lifecycle transitions (rejected versus logged-and-stored) is undecided. The memo names no confirmed mismatch, so the concrete discrepancies are `Needs confirmation`.

## Reason for Change
Deployment and restart behavior drives operator actions. No deadline is known; the work is Medium because no confirmed wrong-action document was identified.

## Implementation Intent
- Read the lifecycle modules and the deployment scripts, then classify each documentation discrepancy using the `rules/coding.md` "Current behavior" classification (accepted specification, documentation fix, implementation fix, already tracked, obsolete).
- Update documents to describe responsibilities and failure behavior, not implementation catalogs.
- File separate issues for any confirmed code defect.

## Target Files or Areas
- `scripts/agent/http_lifecycle.py` and `scripts/agent/http_lifecycle_errors.py` (read for evidence)
- `deploy/` scripts and the actual service-definition location (`Unknown`)
- Deployment documents under `docs/90_deployment/` and recovery documents under `docs/41_db/`
- `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`

## Required Changes
- Document spawn, health probe, restart, cooldown, PID ownership, and shutdown suppression as current behavior.
- Align active database paths and recovery ownership statements across deployment and DB documents.
- Record a decision on invalid lifecycle transitions (reject or log-and-store).
- Add a validated inventory of MCP binaries and service-manager units, generated from live configuration where possible (`tools/generate_mcp_inventory.py`).

## Constraints
- Documentation under `docs/` is English, without literal ports, concrete configuration values, line numbers, or implementation counts (`skills/DESIGN.md`).
- Do not change lifecycle code in this issue.

## Acceptance Criteria
- Each lifecycle behavior listed above is described once, consistently, in the owning document.
- Deployment and recovery documents agree on database paths and recovery ownership.
- The invalid-transition decision is recorded.
- The binary and service-unit inventory is sourced from a checker or generator, not hand-maintained prose.

## Testing Expectations
Not required (documentation-only). Run `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_docs_consistency.py --domain deployment`, and `--domain agent`.

## Documentation Impact
Yes. Intent, responsibility boundaries (Agent versus service manager), failure behavior, operational notes, and Needs Confirmation items.

## Out of Scope
- Changing lifecycle or deployment code.
- Manual recovery procedure changes owned by `adrrev009`.

## Dependencies
Duplicate and overlap check (2026-11-11): no open issue duplicates this one. Overlapping open plans:
- `plans/20261110-233648_adrrev009_adr008-recovery-align.md` (overlap: partial): make manual recovery of `workflow.sqlite` and `eventbus.sqlite` as safe as automated recovery (stop the EventBus service, move `-wal`/`-shm` aside, verify backups), and fix `db_07` and ADR-008 contradictions. This issue's "align database paths and recovery ownership" item may already be covered there; re-check after it lands.
- `plans/20261111-110144_adrrev017_docs-history-wording.md` (overlap: partial): removes history wording from documents including `db_07`, and corrects the FATAL definition in `mcp_06_09`.

Ordering and other dependencies:
- `plans/20261110-233648_adrrev009_adr008-recovery-align.md` edits `db_07`; sequence edits to that file.
- `plans/20261111-110144_adrrev017_docs-history-wording.md` edits several of the same documents; apply this issue after it.

## Unresolved Questions
Decision required from the maintainer before implementation:
- Decision 1 (invalid lifecycle transitions): reject them, or log them and store the state. Rejection is stricter but may block recovery paths.

Open facts (不明):
- 不明: the actual service-definition files and any container entrypoints.
- 不明: which statements in the deployment and DB documents currently contradict the lifecycle code.

## AI Implementation Instruction
- Edit documentation only; base every claim on read source.
- Stop and report when a discrepancy needs a code decision.
- Do not implement out-of-scope items.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261111-163903
- **Related target files**: `scripts/agent/http_lifecycle.py`, `scripts/agent/http_lifecycle_errors.py`, `deploy/`, `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`
