# origin/master's test suite has 579+ failures across at least 10 distinct implementation/test drift clusters

## Priority
High

## Summary
A full `uv run pytest tests/ -q --timeout=20 --ignore=tests/agent/test_repl.py` run against the
current `origin/master` tip (commit `7bc3ed0d0` at time of writing) reports **579 failed, 6399
passed, 16 skipped, 3 errors** out of 7,051 collected tests (`test_repl.py` excluded separately —
see `issues/20260907-140047_repl001_keyboard_interrupt_not_caught_with_shutdown_event.md`, whose
defect also silently truncates full-suite runs that include it). This was discovered incidentally
while validating a routine `git rebase`/push (per `skills/git-commit-and-sync`'s post-sync
validation step), not while working on any of the affected areas. Distinct error signatures
(grouped by `grep -E "^E   "`) indicate at least 10 separate root causes — mostly renamed/removed
attributes, methods, or constructor keyword arguments that the corresponding tests were never
updated for — not one single defect.

## Background
`Explicit in code` (via test output, not yet traced to each specific commit): the largest clusters
by distinct exception signature, with occurrence counts from the run above:

| Count | Signature | Likely cause |
|---|---|---|
| 236 | `SystemExit: 1` (production config validation) | `SecurityProfile` reduced to a single `PRODUCTION` value and `config_builders.py` now defaults `security_profile` to `"production"` — test fixtures using minimal configs (e.g. `test_config_builders.py`'s `_MIN_CFG`) no longer set `tool_definitions_strict`/`routing_drift_strict`, which the fail-closed validator now requires unconditionally. `High confidence` — directly reproduced and diagnosed for `test_config_builders.py`'s 5 failures. |
| 105 | `AttributeError: 'Orchestrator' object has no attribute '_llm_turn_executor'. Did you mean: '_llm_executor'?` | An attribute rename in `Orchestrator` (`_llm_turn_executor` → `_llm_executor` or vice versa) that ~105 call sites across `test_orchestrator.py` and related integration tests were not updated for. `Needs confirmation` — not yet traced to the specific commit or which name is authoritative. |
| 32 | `TypeError: ToolExecutor.__init__() got an unexpected keyword argument 'cache_ttl'` | `ToolExecutor.__init__()`'s signature dropped (or renamed) a `cache_ttl` parameter that tests still pass. `Needs confirmation`. |
| 29 | `sqlite3.OperationalError: no such table: session_diagnostics` | A `session_diagnostics` table referenced by code/tests is missing from whatever schema-creation path the affected tests rely on (possibly a new table added without updating a test fixture's schema setup). `Needs confirmation`. |
| 19 + 6 | `ValueError: McpServerConfig[...]: auth_token must not be empty` | A new non-empty-`auth_token` validation on `McpServerConfig` that multiple test fixtures' server configs don't satisfy. `Needs confirmation`. |
| 10 | `TypeError: audit_security_defaults() got an unexpected keyword argument 'production_mode'` | Signature change on `audit_security_defaults()`. `Needs confirmation`. |
| 8 + 4 | `AttributeError: <module 'agent.startup'> does not have the attribute 'find_all_pending_approvals'` / `'check_workflow_definition'` | Functions removed or renamed out of `scripts/agent/startup.py` that `test_startup.py` still patches/references by the old name. `Needs confirmation`. |
| 5 + 5 | `AttributeError: 'RagIngester' object has no attribute '_get_or_create_document'` / `<class 'rag.ingestion.ingester.RagIngester'> does not have the attribute '_get_embedding'` | Methods renamed or removed from `RagIngester` during a refactor, tests not updated. `Needs confirmation`. |
| 4 | `TypeError: RegistryEntry.__init__() got an unexpected keyword argument 'id'` | Signature change on `RegistryEntry`. `Needs confirmation`. |
| 3 | `AttributeError: module 'rag.pipeline' has no attribute '_ModuleConfig'` | Symbol removed/renamed from `rag.pipeline`. `Needs confirmation`. |

By top-level test file, the highest failure counts are `test_orchestrator.py` (78),
`test_tool_policy.py` (45), `test_startup.py` (45), `commands/test_agent_cmd_session.py` (43),
`test_tool_approval_preflight.py` (40), `integration/test_orchestrator_integration.py` (33),
`test_tool_policy_comprehensive.py` (29), `test_diagnostic_store.py` (29), `test_tool_runner.py`
(27) — a long tail across dozens of files follows.

## Problem
The test suite on `origin/master` does not reflect the current state of the implementation for a
large fraction of the `scripts/agent/` and related test surface. Either several refactors landed
without updating their own tests, or several tests were updated speculatively ahead of an
implementation change that has not (or not fully) landed — this issue does not yet distinguish
which, per cluster. Whichever direction, `origin/master`'s test suite cannot currently be trusted
as a regression gate: a routine rebase validation surfaced 579 failures that evidently were not
caught (or were accepted) before these commits reached `master`.

## Reason for Change
A test suite this far out of sync with the implementation defeats its purpose as a safety net —
any of these ~10 clusters could be masking either a real implementation bug (if the code is wrong
and the test was right) or dead/incorrect test expectations (if the code is right and the test is
stale), and until each cluster is triaged, neither can be assumed. This also means any future
`git-commit-and-sync` post-rebase validation on this branch will report a large, undifferentiated
wall of pre-existing failures, making it hard to spot a *new* regression introduced by unrelated
work.

## Implementation Intent
This issue documents the discovery and provides the initial clustering evidence; it does not
itself resolve any cluster. The recommended next step is to triage each cluster in the table above
— confirm the actual root cause (implementation bug vs. stale test) — and split each into its own
follow-up issue (or a small number of tightly-related issues, per `skills/issue-creator`'s Phase 2
grouping rules) once the direction of the fix (fix the code, or fix the test) is confirmed for
that cluster. Do not attempt a single blanket fix across all clusters — they are unrelated in
cause and in which files must change.

## Target Files or Areas
- `scripts/agent/orchestrator.py`, `tests/agent/test_orchestrator.py`,
  `tests/integration/test_orchestrator_integration.py` (`_llm_turn_executor`/`_llm_executor`
  cluster)
- `scripts/agent/tool_executor.py` or equivalent, `tests/agent/test_tool_policy*.py`,
  `tests/agent/test_tool_runner.py` (`cache_ttl` cluster)
- Whatever module owns `session_diagnostics` schema creation, `tests/agent/test_diagnostic_store.py`
- `scripts/shared/mcp_config.py` (`McpServerConfig`), the many test fixtures constructing it
  without `auth_token`
- `scripts/agent/startup.py`, `tests/agent/test_startup.py`
- `scripts/rag/ingestion/ingester.py` (`RagIngester`), its ingestion tests
- `scripts/rag/pipeline.py` (`_ModuleConfig`)
- Security/audit defaults module owning `audit_security_defaults()`
- `RegistryEntry`'s defining module

## Required Changes
- For each cluster in the Background table: read the actual current implementation, determine
  whether the implementation or the test is authoritative, and either fix the implementation (if
  it regressed) or update the test (if it is stale) — per `skills/python-test-and-fix`'s Core
  Testing Rule "Do Not Fix Tests by Blindly Changing Expectations."
- Re-run the full suite after each cluster's fix to confirm its failure count drops to zero
  without introducing new failures.
- Once all clusters are resolved, confirm `uv run pytest tests/ -q` (including `test_repl.py`,
  once `issues/20260907-140047_repl001_keyboard_interrupt_not_caught_with_shutdown_event.md` is
  fixed) passes cleanly end to end.

## Constraints
- Do not batch unrelated clusters into one commit/PR — each has a different root cause and a
  different correct fix direction.
- Do not "fix" a failing test by weakening its assertion without first confirming the
  implementation behavior it checks is actually still correct per the system's contract.
- Do not assume every cluster is a stale test — some (e.g. the `session_diagnostics` missing
  table) may indicate a real migration/schema gap that would also affect production.

## Acceptance Criteria
- [ ] Each cluster in the Background table has a `Needs confirmation` → `Confirmed` root-cause
      determination (implementation bug or stale test), recorded either in a follow-up issue or
      directly in this issue if resolved without one.
- [ ] `uv run pytest tests/ -q` (full suite, `test_repl.py` included once its separate defect is
      fixed) reports 0 failures attributable to any cluster listed here.
- [ ] No new failure is introduced by any cluster's fix (confirmed by a full-suite re-run after
      each fix).

## Testing Expectations
Full-suite `uv run pytest tests/ -q` re-run after each cluster's fix; targeted runs of the
specific files in the Background table during triage of each cluster.

## Documentation Impact
None expected directly from this tracking issue; individual cluster fixes may require doc updates
if they touch a documented contract (e.g. `McpServerConfig`'s `auth_token` requirement, if that
validation is new and intended, should be reflected in relevant `docs/adr/*.md` or config
reference docs — confirm per-cluster during triage).

## Out of Scope
- `tests/agent/test_repl.py`'s `KeyboardInterrupt` defect — tracked separately in
  `issues/20260907-140047_repl001_keyboard_interrupt_not_caught_with_shutdown_event.md`.
- Any cluster not represented in the Background table (this table reflects one run's signature
  grouping at `--timeout=20`; a different random test order or a rerun after partial fixes may
  surface additional signatures not listed here — re-run and re-cluster as fixes land).

## Dependencies
N/A: none directly, though resolving
`issues/20260907-140047_repl001_keyboard_interrupt_not_caught_with_shutdown_event.md` first makes
full-suite verification of this issue's fixes more reliable (a full run currently risks an early
session abort from that separate defect).

## Unresolved Questions
- For each `Needs confirmation` cluster in the Background table: which side (implementation or
  test) is authoritative, and which specific commit introduced the drift — not yet investigated
  beyond the error signature itself.
- Whether `origin/master`'s CI actually runs the full `tests/` suite on every merge, and if so, why
  579 failures were not caught before landing — this issue only reports the current state, not why
  it was not caught upstream; that is a separate process question the user may want to raise
  independently.

## AI Implementation Instruction
Do not attempt to fix all ~10 clusters in one pass. Triage one cluster at a time: read the current
implementation the failing tests target, determine authoritative behavior, fix accordingly, and
re-run only that cluster's tests before moving to the next. If a cluster's root cause turns out to
be broader or riskier than its error signature suggests (e.g. the `session_diagnostics` missing
table turning out to be a real production migration gap), stop and file that specific finding as
its own higher-priority issue rather than folding it into a "test fix."
