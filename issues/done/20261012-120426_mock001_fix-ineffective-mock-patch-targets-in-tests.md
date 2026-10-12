# Fix ineffective mock patch targets in tests

## Priority
Medium

## Summary
`tools/check_mock_patch_targets.py` reports 23 `ineffective-patch-target` findings at 11 `patch(...)` call sites in 6 test files. Each site patches the symbol on its origin module, while the module under test holds its own module-level binding of that symbol, so the mock may never be seen by the code under test. Triage every site, then make each patch effective, remove it when redundant, or record why it is a false positive, so that the checker reports no findings.

## Background
- `tools/check_mock_patch_targets.py` is a heuristic, report-only lint (exit code 0 even with findings). It flags `patch("origin.Symbol")` when a candidate module under test imports `Symbol` from `origin` at module level.
- The finding count was measured on `master` at commit `df93c4215` when the report-only checkers not wired into pre-commit were surveyed: 23 findings, all of category `ineffective-patch-target`, no other categories.
- The 23 findings collapse to 11 call sites because one `patch` call is reported once per importing module. Sites per file:
  - `tests/agent/commands/test_agent_cmd_memory.py` lines 348, 369, 404 (`db.helper.SQLiteHelper`)
  - `tests/agent/commands/test_memory_consistency.py` lines 167, 175 (`db.helper.SQLiteHelper`)
  - `tests/agent/memory/test_memory_store.py` line 147 (`db.helper.SQLiteHelper`)
  - `tests/agent/test_llm_turn_runner.py` line 147 (`agent.message_schema.validate_message`)
  - `tests/agent/test_startup_approval_recovery.py` lines 649, 690, 817 (`shared.logger.Logger`)
  - `tests/mcp_servers/git/test_git_security_compliance.py` line 696 (`mcp_servers.audit._audit_log`)
- `tools/check_mock_patch_targets.py` documents this pattern as recurring in this repository (its module docstring cites `tests/agent/test_diagnostic_store.py` as an earlier instance).
- No open issue under `issues/` covers these tests; the five open files there are design memos unrelated to test patching.

## Problem
- Python resolves `from origin import Symbol` once at import time. Patching `origin.Symbol` afterwards does not change the binding already held by the importing module, so the test may exercise the real symbol instead of the mock.
- Evidence (`Explicit in code`) for the strongest cases:
  - `tests/agent/test_startup_approval_recovery.py` patches `shared.logger.Logger`, but `scripts/agent/startup.py` creates `logger = Logger(__name__, ...)` at module import time, so the patch cannot affect that logger. The tests then assert on `mock_logger.return_value.warning.call_args_list`, which stays empty; any assertion that only filters or counts matching calls can pass without checking anything.
  - `tests/mcp_servers/git/test_git_security_compliance.py` patches `mcp_servers.audit._audit_log`, but `scripts/mcp_servers/git/git_server.py` binds `_audit_log` through `from mcp_servers.audit import _audit_log`. The test inspects `mock_audit` only inside `if mock_audit.called:`, so the audit assertions are skipped silently when the patch is ineffective.
- Evidence (`Explicit in code`) for the weaker cases:
  - `tests/agent/memory/test_memory_store.py` line 147 already patches `agent.memory.store.SQLiteHelper` and `agent.memory.count_ops.SQLiteHelper` separately; the origin patch is only needed for modules not covered by those two (the checker also names `agent.memory.write_ops`).
  - `tests/agent/commands/test_memory_consistency.py` line 175 additionally replaces the bound references on `import_ops` and `write_ops` by hand, so part of that fixture is already compensating.
- Needs confirmation: whether each remaining site passes because the real symbol behaves acceptably in the test environment, or because the assertion is vacuous. This cannot be read from the checker output alone.

## Reason for Change
- Testability and correctness of the test suite: a test that patches the wrong target can pass while verifying nothing, so regressions in the covered behavior (memory pruning/import, startup approval recovery, git audit logging) would go unnoticed.
- One site is a security compliance test (git audit logging on a rejected repository path), where a skipped audit assertion weakens the evidence the test is meant to provide.
- The recurring pattern is already detected by `tools/check_mock_patch_targets.py`, but the checker is not wired into pre-commit or CI because of these findings; clearing them is the precondition for gating it.

## Implementation Intent
- Treat each of the 11 call sites individually. For each, decide one of:
  - retarget the patch to the module that performs the lookup (the name the code under test actually resolves), or
  - remove the patch when the behavior it replaces is covered elsewhere, or
  - keep it and record why the checker's finding is a false positive (for example a function-local import that re-resolves on every call).
- Where the symbol is bound at import time and cannot be retargeted cleanly (module-level `logger = Logger(...)` in `agent.startup`), prefer patching the already-created object's behavior or asserting through the standard logging capture, rather than patching the class.
- Replace vacuous assertion shapes that hide an ineffective patch (such as asserting only inside `if mock.called:`) with an unconditional assertion, so a future ineffective patch fails loudly.
- Preserve the intent and the tested behavior of every test; change only how the substitute is installed and how it is asserted.

## Target Files or Areas
- `tests/agent/commands/test_agent_cmd_memory.py`
- `tests/agent/commands/test_memory_consistency.py`
- `tests/agent/memory/test_memory_store.py`
- `tests/agent/test_llm_turn_runner.py`
- `tests/agent/test_startup_approval_recovery.py`
- `tests/mcp_servers/git/test_git_security_compliance.py`
- `tools/check_mock_patch_targets.py` (read-only reference for the finding semantics; change only if a site is confirmed as a checker false positive that cannot be expressed otherwise)

## Required Changes
- For each of the 11 call sites, record the triage outcome (retarget, remove, or false positive with reason) in the plan or in the commit message.
- Fix the ineffective patches so each substitute is installed where the code under test looks the name up.
- Make the assertions that depend on a mock unconditional where they are currently guarded by `if mock.called:` or filter an always-empty call list.
- Re-run the affected tests after each file and confirm that no test is silently relying on the real symbol.
- If a test starts failing once its patch becomes effective, report it as a separate finding instead of weakening the assertion.

## Constraints
- Do not change production code under `scripts/` to make a patch effective; the fix belongs in the tests. If a test cannot be made effective without a production change, record it under Unresolved Questions and stop for that site.
- Keep each test's tested behavior and name stable; follow `rules/coding.md` conventions (English comments, ruff line length).
- The checker is a heuristic: a site cleared by triage as a false positive must not be hidden by editing the checker's detection rules unless the heuristic itself is demonstrably wrong.

## Acceptance Criteria
- `uv run python tools/check_mock_patch_targets.py` reports 0 findings, or every remaining finding has a recorded false-positive reason accepted in review.
- For each of the 11 call sites, the patched object is the one the code under test uses: a deliberate change of the production symbol's behavior makes the corresponding test fail (checked once per file, then reverted).
- No assertion that depends on a mock remains guarded by `if mock.called:` in `tests/mcp_servers/git/test_git_security_compliance.py`.
- The 6 affected test files pass: `uv run pytest tests/agent/commands/test_agent_cmd_memory.py tests/agent/commands/test_memory_consistency.py tests/agent/memory/test_memory_store.py tests/agent/test_llm_turn_runner.py tests/agent/test_startup_approval_recovery.py tests/mcp_servers/git/test_git_security_compliance.py`.
- The full suite shows no new failures compared with `master` before the change.

## Testing Expectations
- Run the 6 affected test files after each file's change, then the full suite once at the end (`uv run pytest`).
- Run `uv run python tools/check_mock_patch_targets.py` before and after and compare the finding list.
- For each file, perform one mutation check: temporarily break the production behavior the test is meant to cover, confirm the test fails, and revert the mutation.
- Run the validation sequence in `rules/toolchain.md` (ruff, mypy for `scripts/`, pre-commit) before committing.

## Documentation Impact
- No documentation under `docs/` is expected to change.
- If the checker's detection rules are changed because a site is a confirmed false positive, update `tools/TOOL_DESCRIPTIONS.md` in the same change.

## Out of Scope
- Wiring `tools/check_mock_patch_targets.py` into `.pre-commit-config.yaml` or CI, and making it exit non-zero; do that as a follow-up once the finding count is 0.
- Changes to production code under `scripts/`.
- Reviewing other tests that the checker does not flag.
- Refactoring the test fixtures beyond what is needed to make each patch effective.

## Dependencies
- Depends on no other issue. Sibling-issue check: the five open files under `issues/` are design memos and do not touch these tests.
- Follow-up (not part of this issue): gate `tools/check_mock_patch_targets.py` in pre-commit after this issue is resolved.

## Unresolved Questions
- Whether each site currently passes for the right reason or vacuously is unknown and must be established per site during planning.
- Whether `tests/agent/test_llm_turn_runner.py` line 147 is a false positive is unknown: `scripts/agent/llm_turn_runner.py` imports `validate_message` inside a function (re-resolved per call), while `scripts/agent/context.py` imports it at module level; which of the two paths the test exercises is not confirmed.
- Priority is set to Medium (testability). It would be High if triage shows the git audit compliance test has been silently skipping its audit assertions in a way that hides a real audit gap; this is not confirmed.

## AI Implementation Instruction
- Change only the 6 test files listed under Target Files or Areas; do not edit unrelated tests, fixtures, or production code.
- Triage one call site at a time and record the outcome before editing it.
- Do not weaken or delete an assertion to make a test pass; if a test fails once its patch is effective, stop and report it.
- Do not edit the checker's detection logic to hide a finding unless the heuristic is shown to be wrong for that pattern.
- Stop and report open questions instead of guessing when a site cannot be made effective without a production change.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261012-120426
- **Related target files**: tests/agent/commands/test_agent_cmd_memory.py, tests/agent/commands/test_memory_consistency.py, tests/agent/memory/test_memory_store.py, tests/agent/test_llm_turn_runner.py, tests/agent/test_startup_approval_recovery.py, tests/mcp_servers/git/test_git_security_compliance.py
