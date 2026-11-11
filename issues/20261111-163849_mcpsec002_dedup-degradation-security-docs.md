# Align MCP dedup degradation behavior and security documentation

## Priority
Medium

## Summary
Document the retry-class-dependent degradation of the durable dedup store, decide whether a retryable tool may execute after a failed `record_pending`, and add an operational signal for dedup-store degradation, without duplicating the frozen `adrrev011` audit and authentication scope.

## Background
Source: `memo-issue.md` (Issue D), re-verified against current source on 2026-11-11.

- `Explicit in code`: `scripts/mcp_servers/dispatch.py` carries a `dedup_state` result field with the values `store_error` and `unreplayable`, a `dedup_store_error` outcome for non-retryable tools when the durable store is unavailable, and a `_store_op()` helper that returns a boolean for each store operation.
- `Documentation only` (memo): initialization failure degrades retryable tools to overlay-only execution; non-retryable side-effecting tools fail closed; several callers continue after a failed store mutation, which can leave a retryable mutation executing without durable pending or completed state. The per-caller behavior was not re-read in this pass (`Needs confirmation`).
- Keyless side-effect handling is covered by the sibling MCP route issue, not here.

## Problem
The degradation behavior depends on the tool's retry class and on which store operation failed, and it is not fully documented. There is no confirmed operational metric or event for degradation, and the behavior for a failed `record_pending` on a retryable tool is undecided.

## Reason for Change
Operators cannot currently tell from documentation or signals when dedup protection is degraded. This is a non-critical documentation and observability gap; it is Medium because the fail-closed path for non-retryable tools already exists.

## Implementation Intent
- Write the retry-class-dependent behavior as a current-tense policy in the security and MCP documents, with ADR-004 as the failure-policy authority.
- Decide the `record_pending` failure policy and, if it changes behavior, split that code change into its own plan.
- Add an operational signal (metric or event) at the existing monitoring integration point for initialization, lookup, and write degradation.

## Target Files or Areas
- `scripts/shared/mcp_dedup.py` and `scripts/mcp_servers/dispatch.py` (behavior evidence)
- `config/mcp_dedup.toml` (retry classes; read only)
- `tests/mcp_servers/test_mcp_dispatch.py` (existing overlay and fail-closed contract)
- Monitoring integration under `config/`, `deploy/`, or `scripts/ops/` (`Unknown`)
- MCP audit and protected-asset documents under `docs/22_mcp/`, and the security documents under `docs/`

## Required Changes
- Document the exact retry-class-dependent degradation behavior and the protected-asset and health-mechanism claims.
- Emit an operational metric or event for durable-store initialization, lookup, and write degradation.
- Decide whether a failed `record_pending` for a retryable tool executes or fails closed, and record the decision (ADR-004 exception or plan).
- Keep disabled-tool rejection semantics distinct from executed-call audit in the documentation.

## Constraints
- Do not duplicate the frozen scope of `plans/20261111-095422_adrrev011_mcp-audit-auth-adr.md` (RAG audit and authentication ADR).
- Documentation must not copy concrete configuration values (`skills/DESIGN.md` No concrete configuration values).
- A behavior change for `record_pending` requires a maintainer decision first.

## Acceptance Criteria
- The degradation behavior per retry class and per failed store operation is documented and agrees with the code and ADR-004.
- A degradation event or metric exists and is documented, or a recorded decision explains why not.
- The `record_pending` policy decision is recorded.
- Documentation consistency checkers pass.

## Testing Expectations
- If code behavior or signals change: unit tests in `tests/mcp_servers/test_mcp_dispatch.py` for each degradation branch and the emitted signal.
- Documentation checks: `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_consistency.py --domain mcp`, `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_known_deviation_sync.py`.

## Documentation Impact
Yes. Update MCP audit, protected-asset, and health-mechanism documents: intent, failure behavior per retry class, Known Issues, and Needs Confirmation items.

## Out of Scope
- RAG audit emission and MCP authentication (`adrrev011`).
- Dedup store ownership and configuration split (`adrrev008`).
- Keyless side-effect rejection (sibling MCP route issue).

## Dependencies
Duplicate and overlap check (2026-11-11): no open issue duplicates this one. Overlapping open plans:
- `plans/20261110-230633_adrrev008_mcp-dedup-ownership.md` (overlap: partial, largest): classify `mcp_dedup.sqlite` as a disposable cache, reject non-retryable tools (fail closed) when the store is lost or recreated, register the two remaining degradation paths under an approved ADR-004 exception, and split `config/mcp_dedup.toml` per process. The non-retryable fail-closed and exception parts of this issue's documentation work are already planned there; only the retryable-tool `record_pending` decision, the degradation signal, and remaining document alignment are new here.
- `plans/20261111-095422_adrrev011_mcp-audit-auth-adr.md` (overlap: partial): RAG audit record emission and a new MCP authentication ADR. Out of scope here.

Ordering and other dependencies:
- Re-verify against `adrrev008` after it lands, and sequence document edits with `adrrev011`.
- Related: `issues/20261111-163724_mcproute001_remove-direct-mcp-routes.md` owns keyless side-effect rejection.

## Unresolved Questions
Decision required from the maintainer before implementation:
- Decision 1 (`record_pending` failure): when `record_pending` fails for a retryable tool, either execute without durable state (current behavior in some callers) or fail closed. Failing closed gives stronger dedup but lowers availability.

Open facts (不明):
- 不明: the monitoring integration point for degradation signals.
- 不明: how much of the described behavior `adrrev008` already documents once it lands.
- Assumption: ADR-004 remains the failure-policy authority.

## AI Implementation Instruction
- Limit changes to documentation and the degradation signal; do not alter dedup behavior without a recorded decision.
- Stop and report if `adrrev008` has already covered a requirement.
- Do not implement out-of-scope items.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261111-163849
- **Related target files**: `scripts/shared/mcp_dedup.py`, `scripts/mcp_servers/dispatch.py`, `config/mcp_dedup.toml`, `tests/mcp_servers/test_mcp_dispatch.py`
