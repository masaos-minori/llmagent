# Remove workflow legacy recovery compatibility and single-value FailurePolicy

## Priority
Medium

## Summary
Remove the remaining workflow-recovery compatibility code and tests (lease-less legacy recovery, retained legacy-row tests) and the single-value `FailurePolicy` indirection, under the repository's current-schema-only and no-shim policy, without duplicating the RAG and EventBus cleanups already filed.

## Background
Source: `memo-issue.md` (Issue E), narrowed after a sibling check on 2026-11-11.

- `Explicit in code`: `scripts/agent/workflow/state_store.py` defines `_LEGACY_STALE_AGE_SEC` and reports `legacy_recovered`; recovery handles lease-less attempts older than that age.
- `Explicit in code`: `tests/agent/workflow/test_workflow_state_store.py` contains legacy tests: a pre-existing composite-key row test and lease-less recovery tests asserting `legacy_recovered`. The memo cites `tests/test_workflow_state_store.py`, which does not exist.
- `Explicit in code`: `FailurePolicy` or `failure_policy` appears in `scripts/shared/mcp_config.py` and `scripts/agent/startup_reporter.py`. Whether it is a single-valued policy is `Needs confirmation`.
- Sibling coverage: `issues/20261110-170632_rmcompat001_rag-delegation-leftovers.md` through `issues/20261110-171157_rmcompat008_compat-checker-patterns.md` already cover RAG, EventBus, history-comment, and checker cleanup. No open issue mentions the workflow legacy tests, `legacy_recovered`, or `FailurePolicy`.
- Memo items not carried here because other issues own them: `ToolConfig.tool_definitions` consumers and `tool_constants.py` comments belong to `issues/20261111-163741_rtregistry001_runtime-registry-sole-authority.md` and `issues/20261111-163800_sideeffect001_side-effect-classification-central.md`; RAG and EventBus items belong to the rmcompat issues.
- Memo items not verified: the `scripts/db/wal_checkpoint_manager.py` path from the memo does not exist, and the mode and Memory cleanup scopes are unconfirmed.

## Problem
Compatibility code for pre-lease workflow rows and retained-database tests remains although the repository policy is current-schema only, and a possibly single-valued failure-policy abstraction adds indirection. Each leftover keeps an unreachable branch alive and must be reasoned about in recovery work.

## Reason for Change
The recovery transaction is being documented (see the ADR-001 issue); removing the legacy branch first simplifies that description. No deadline; the cleanup is Medium maintainability work.

## Implementation Intent
- Remove the lease-less legacy recovery branch, `_LEGACY_STALE_AGE_SEC`, `legacy_recovered`, and the tests that exist only to pin them, after confirming no production row can lack a lease.
- Reconcile retained-database compatibility tests with the current-schema-only policy.
- Remove `FailurePolicy` indirection only if it proves single-valued.
- Use `tools/check_compat_shims.py` as the completion check.

## Target Files or Areas
- `scripts/agent/workflow/state_store.py`
- `tests/agent/workflow/test_workflow_state_store.py`, `tests/agent/workflow/test_state_store.py`, `tests/agent/workflow/test_stale_recovery_lease.py`
- `scripts/shared/mcp_config.py`, `scripts/agent/startup_reporter.py` (`FailurePolicy` references; repository-wide search required)
- Schema and compatibility plans under `plans/` and `plans/done/` (ownership check)

## Required Changes
- Confirm the schema owner and that lease-less rows cannot exist, then remove the legacy recovery branch, constant, report field, and legacy-only tests.
- Remove or rewrite retained-database compatibility tests for legacy composite task keys and legacy snapshot columns.
- Run a repository-wide `FailurePolicy` and `failure_policy` search; remove the abstraction if single-valued, otherwise record why it stays.

## Constraints
- Current-schema-only policy: no migration shim (`rules/persisted-schema-change.md` if schema is touched).
- Follow the deprecation policy in `rules/coding.md`; confirm zero callers with `rg` before removal.
- Do not change recovery semantics for lease-bearing attempts or task reconciliation.

## Acceptance Criteria
- No `_LEGACY_STALE_AGE_SEC`, `legacy_recovered`, or lease-less recovery path remains.
- Remaining workflow tests cover only the current schema and the lease-based recovery.
- `FailurePolicy` is removed or its retention is documented.
- `uv run python tools/check_compat_shims.py` passes.

## Testing Expectations
- Run `uv run pytest tests/agent/workflow/ -v`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `uv run ruff check scripts/`, `uv run vulture scripts/ --min-confidence 80`, and `uv run python tools/check_compat_shims.py`.
- Apply the `rules/toolchain.md` impact-radius check (`rg -l` counts) before removing `FailurePolicy`.

## Documentation Impact
Yes, if ADR-001 or the workflow and DB documents mention lease-less recovery: update them to the lease-only rule. No other documentation change.

## Out of Scope
- RAG, EventBus DLQ, history-comment, and checker items owned by the rmcompat issues.
- `tool_definitions` and `tool_constants.py` changes.
- WAL, mode, and Memory compatibility cleanup until their targets are confirmed in a separate issue.

## Dependencies
Duplicate and overlap check (2026-11-11): no open issue duplicates this one (the workflow legacy tests, `legacy_recovered`, and `FailurePolicy` appear in no open issue or plan). Related open issues that cover other parts of the memo's compatibility list and are intentionally not repeated here:
- `issues/20261110-170632_rmcompat001_rag-delegation-leftovers.md`: finish removing the remote RAG delegation path (configuration key, unused ingester state, `__del__` cleanup, stale startup warning).
- `issues/20261110-170709_rmcompat002_rag-diagnostics-model.md`: merge the two RAG `SearchDiagnostics` classes into one model.
- `issues/20261110-170753_rmcompat003_rag-corpus-identity-decision.md`: decide whether to keep the RAG corpus identity and remove placeholder branches.
- `issues/20261110-170832_rmcompat004_eventbus-config-auth-audit.md`: single validation, one authorization format, and complete audit records in EventBus.
- `issues/20261110-170926_rmcompat005_eventbus-dlq-leftovers.md`: remove unreachable DLQ code and redundant result fields.
- `issues/20261110-171004_rmcompat006_rag-ingestion-cleanup.md`: remove or justify stale `type: ignore` comments and tolerant reads in RAG ingestion.
- `issues/20261110-171040_rmcompat007_history-comment-sweep.md`: sweep history comments and plan identifiers in `scripts/` and `config/` after the other cleanups land; sequence this issue before it.
- `issues/20261110-171157_rmcompat008_compat-checker-patterns.md`: extend `tools/check_compat_shims.py` with the leftover phrases; new patterns may flag items here.

Ordering and other dependencies:
- Coordinate with `issues/20261111-163819_wfrecov001_adr001-recovery-reconciliation.md`: the ADR wording refers to the legacy branch; this issue removes it.
- `plans/20261111-110144_adrrev017_docs-history-wording.md`: edits ADR-001 wording; re-verify afterward.
- Ownership of retained-database compatibility removal: `plans/done/20261110-095137_adrrev005_schema-fingerprint-unify.md` is archived; confirm nothing remains open for it.

## Unresolved Questions
Decision required from the maintainer before implementation:
- Decision 1: whether any deployed database can still hold lease-less attempt rows. If it can, legacy recovery removal needs an operator step first; this decides whether removal may proceed.

Open facts (不明):
- whether `FailurePolicy` is single-valued and who consumes it.
- 不明: the real WAL checkpoint module path and whether any WAL, mode, or Memory compatibility remains; file a separate issue if so.

## AI Implementation Instruction
- Remove only the confirmed leftovers; keep the diff minimal and run the `rg` zero-caller check first.
- Stop and report if a production row can still lack a lease.
- Do not implement out-of-scope items.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261111-163923
- **Related target files**: `scripts/agent/workflow/state_store.py`, `tests/agent/workflow/test_workflow_state_store.py`, `tests/agent/workflow/test_state_store.py`, `tests/agent/workflow/test_stale_recovery_lease.py`, `scripts/shared/mcp_config.py`, `scripts/agent/startup_reporter.py`
