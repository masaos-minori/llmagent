# mcp_tool_discovery escalates per-entry WARNING findings to FATAL for required servers, contradicting its own docstring and tests

## Priority
High

## Summary
`scripts/agent/services/mcp_tool_discovery.py`'s `_validate_and_normalize_entry()`
docstring states "Schema errors are per-tool WARNING findings, not FATAL", and its helper
`_warning_entry()` always builds a `StartupCheckStatus.WARNING` finding. But
`_fetch_server_tools()` (the caller) escalates any such finding to
`StartupCheckStatus.FATAL` whenever `cfg.required` is true:

```
normalized, finding = self._validate_and_normalize_entry(key, cfg.url, raw_entry)
if finding is not None and cfg.required:
    finding = StartupCheckOutcome(..., status=StartupCheckStatus.FATAL, ...)
```

`McpServerConfig.required` defaults to `True`. 2 tests in
`tests/agent/services/test_mcp_tool_discovery.py` construct servers via the file's
`_server()` helper (which does not override `required`), expect the resulting finding's
`status` to be `WARNING` per the docstring, and fail because it is actually `FATAL`.

**Adversarial verification note**: an earlier version of this issue claimed "4 tests
... fail because [of this]." Verified by running the full test file
(`uv run pytest tests/agent/services/test_mcp_tool_discovery.py -q`): 4 tests do fail,
but only 2 —
`test_enabled_type_checked_when_present_synthetic` and
`test_malformed_capabilities_produces_warning_not_fatal` — are actually caused by this
issue's described WARNING→FATAL escalation (confirmed: both use `_server()`'s default
`required=True`, submit a malformed tool entry, and fail at
`assert ... .status == StartupCheckStatus.WARNING` with the actual value `FATAL`). The
other 2 —
`TestDiscoverAllCrossProfileEquivalence::test_classification_equivalent_across_security_profiles[True-fatal-production]`
and `[False-warning-production]` — fail on a different, earlier assertion
(`assert result.unreachable == ["srv"]`, actual `[]`) and are an unrelated bug: see
Out of Scope.

## Background
Confirmed via a `git worktree` checkout of `origin/master` at commit `df4a58671` that this
reproduces identically on that commit alone, unrelated to this session's own (Agent/
EventBus reference-table) work rebased on top of it afterward.

## Problem
It is unclear from the code alone which side is the intended, current design: the
docstring/tests (per-tool schema issues should always be WARNING, never FATAL), or the
escalation logic (a required server's malformed tool entry should be FATAL, blocking
startup). As written, the escalation logic wins at runtime, silently contradicting the
documented contract in `_validate_and_normalize_entry()`'s own docstring. If the
escalation is the correct, intended behavior, a single malformed tool entry from any
`required=True` server (the default for every server unless explicitly overridden) will
FATAL-block agent startup — a much stronger blast radius than "per-tool WARNING findings,
not FATAL" implies to a reader of that docstring.

**Adversarial verification note — this question is resolved, with evidence**: see
Unresolved Questions below. The escalation is confirmed intentional; the docstring is
the stale side.

## Reason for Change
A docstring that contradicts the actual runtime behavior is itself a defect (misleads any
future maintainer reading `_validate_and_normalize_entry()` in isolation), and the current
runtime behavior may be an unintended over-escalation that could FATAL-block agent startup
for a minor, single-tool schema issue on any server that has not explicitly set
`required=False`.

## Implementation Intent
**Resolved by adversarial verification (see Unresolved Questions for evidence):**
escalation to FATAL for required servers is intentional (REQ-008). Apply only the
second of the two originally-proposed branches:
- Correct `_validate_and_normalize_entry()`'s docstring to state the actual behavior
  explicitly (per-tool schema errors are WARNING findings for `required=False`
  servers, escalated to FATAL for `required=True` servers — matching REQ-008's
  documented intent).
- Update the 2 tests this issue's mechanism actually causes to fail
  (`test_enabled_type_checked_when_present_synthetic`,
  `test_malformed_capabilities_produces_warning_not_fatal`) to expect `FATAL`, since
  both use `_server()`'s default `required=True`.
- Add a `required=False` case for at least one of these two scenarios (e.g. a
  parametrized variant or a new test) expecting `WARNING`, so both branches remain
  covered per Constraints.
Do not remove or narrow the escalation block in `_fetch_server_tools()` — that would
contradict the confirmed, deliberate, security-motivated design (REQ-008).

## Target Files or Areas
- `scripts/agent/services/mcp_tool_discovery.py` (`_validate_and_normalize_entry`
  docstring only — `_fetch_server_tools`'s escalation logic is confirmed correct and
  must not change)
- `tests/agent/services/test_mcp_tool_discovery.py` (2 tests using `_server()`'s default
  `required=True`: `test_enabled_type_checked_when_present_synthetic`,
  `test_malformed_capabilities_produces_warning_not_fatal`; plus one new/extended
  `required=False` case)

## Required Changes
- Apply the fix from Implementation Intent above: correct the docstring, update the 2
  named tests to expect `FATAL`, add a `required=False` case expecting `WARNING`.
- The investigation step (git history of the escalation block vs. the docstring) is
  already done — see Unresolved Questions for the evidence trail; no further
  investigation is required before implementing.

## Constraints
Whatever the resolution, both `required=True` and `required=False` server configurations
must have explicit, tested coverage for this escalation behavior afterward — do not leave
only one branch covered.

## Acceptance Criteria
- `test_enabled_type_checked_when_present_synthetic`,
  `test_malformed_capabilities_produces_warning_not_fatal`, and the new
  `required=False`-expects-`WARNING` case all pass.
- `_validate_and_normalize_entry()`'s docstring accurately describes the actual runtime
  severity behavior for both `required=True` and `required=False` servers.

**Correction (adversarial verification)**: the original criterion —
`uv run pytest tests/agent/services/test_mcp_tool_discovery.py -q` reports 0 failures —
is not achievable by this issue's fix alone. 2 of the file's 4 current failures
(`TestDiscoverAllCrossProfileEquivalence::test_classification_equivalent_across_security_profiles`,
both parametrizations) are an unrelated bug (see Out of Scope) that this issue does not
fix. The criteria above are scoped to this issue's actual target.

## Testing Expectations
Run `uv run pytest tests/agent/services/test_mcp_tool_discovery.py::test_enabled_type_checked_when_present_synthetic tests/agent/services/test_mcp_tool_discovery.py::test_malformed_capabilities_produces_warning_not_fatal -q`
plus the new `required=False` test. Running the full
`uv run pytest tests/agent/services/test_mcp_tool_discovery.py -q` afterward is
expected to still report 2 failures (the unrelated `TestDiscoverAllCrossProfileEquivalence`
ones — see Out of Scope), not 0 — do not treat that as a regression. Also run the full
`uv run pytest tests/ -q` to confirm no *new* failures are introduced elsewhere
(comparing against the pre-existing baseline, not against a 0-failure target).

## Documentation Impact
If the resolution changes `_validate_and_normalize_entry()`'s docstring, check whether any
`docs/*.md` file describing MCP tool discovery startup-check severity needs the same
correction (per `routing.md`'s Documentation row) — not investigated as part of this
issue.

## Out of Scope
Any other failing test file identified in the same investigation
(`tests/agent/test_orchestrator.py`, `tests/agent/services/test_config_reload.py`,
`tests/eventbus/test_eventbus_auth.py`,
`tests/mcp_servers/git/test_git_security_compliance.py`) — each is tracked as its own
issue.

Also out of scope: 2 other, unrelated failures within `test_mcp_tool_discovery.py`
itself —
`TestDiscoverAllCrossProfileEquivalence::test_classification_equivalent_across_security_profiles[True-fatal-production]`
and `[False-warning-production]` (see Summary's adversarial-verification note). Root
cause (confirmed by reading `McpServerConfig`/`discover_all()`): the test constructs
`McpServerConfig(transport=TransportType.HTTP, url=..., required=required_value,
auth_token=...)` directly, without `_server()`'s `startup_mode=StartupMode.PERSISTENT`
default — `McpServerConfig.startup_mode` itself defaults to `StartupMode.NONE`, which
makes `cfg.is_disabled` (`startup_mode == StartupMode.NONE`) `True`, so
`discover_all()`'s `if cfg.transport != TransportType.HTTP or not cfg.url or
cfg.is_disabled: continue` skips the server entirely before `_fetch_server_tools()` is
ever called — hence `result.unreachable == []` instead of `["srv"]`. This is a
test-fixture bug (a missing `startup_mode=StartupMode.PERSISTENT` argument), unrelated
to the WARNING/FATAL docstring contradiction this issue addresses. Not fixed here to
keep this issue's diff minimal — a one-line follow-up fix (or its own issue) is
recommended.

## Dependencies
N/A: none.

## Unresolved Questions
N/A: resolved by adversarial verification, with git-history evidence.

**Resolution**: escalate-to-FATAL-when-required is the intended design; the docstring
is stale. Evidence:
- `git log -S"status=StartupCheckStatus.FATAL" --oneline -- scripts/agent/services/mcp_tool_discovery.py`
  identifies commit `0e05e9adf` ("feat(agent): add disabled-server exclusion,
  required-tool FATAL escalation, and tool-presence check (REQ-001/008/009)") as the
  commit that introduced the `if finding is not None and cfg.required:` escalation
  block — confirmed via `git show 0e05e9adf -- scripts/agent/services/mcp_tool_discovery.py`.
- The file's original creation commit (`3ea7d883c`, `git show 3ea7d883c:scripts/agent/services/mcp_tool_discovery.py`)
  already contains the "Schema errors are per-tool WARNING findings, not FATAL"
  docstring text and has **no** `cfg.required` reference anywhere — the escalation
  block did not exist yet. The docstring predates the escalation feature by several
  commits; they did not move together, and the docstring was never updated when
  REQ-008 landed.
- `implementations/done/20260916-154416_01_scripts_agent_services_mcp_tool_discovery.md`
  (the implementation procedure for commit `0e05e9adf`) states the intent explicitly:
  "Extend `_validate_and_normalize_entry()`'s caller to escalate malformed entries
  belonging to a `required=True` server to FATAL instead of WARNING. (REQ-008)"; its
  Compatibility/Security considerations state "The FATAL escalation for
  required-server malformed entries (REQ-008) may turn previously-WARNING-only
  production deployments into one that fails to start ... **This is the Issue's
  explicit intent**" and "Escalating malformed entries on required servers to FATAL
  ensures that a compromised or misconfigured server cannot silently degrade security
  posture."
- `McpServerConfig.required`'s own field comment
  (`scripts/shared/mcp_config.py:102`) already documents this exact purpose:
  `required: bool = True  # Startup criticality: FATAL vs WARNING escalation at discovery`.

This resolves Implementation Intent's second branch as the correct fix: correct the
docstring, not the escalation logic.

## AI Implementation Instruction
The investigation is already done (see Unresolved Questions) — escalation to FATAL for
required servers is confirmed intentional (REQ-008). Correct
`_validate_and_normalize_entry()`'s docstring to state this, update only the 2 named
tests (`test_enabled_type_checked_when_present_synthetic`,
`test_malformed_capabilities_produces_warning_not_fatal`) to expect `FATAL`, and add a
`required=False` case expecting `WARNING`. Do not touch `_fetch_server_tools()`'s
escalation logic itself, and do not touch
`TestDiscoverAllCrossProfileEquivalence::test_classification_equivalent_across_security_profiles`
— its 2 failures are a separate, unrelated bug (see Out of Scope). Keep the diff
minimal and scoped to this file pair.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260919-164314
- **Related target files**: scripts/agent/services/mcp_tool_discovery.py, tests/agent/services/test_mcp_tool_discovery.py
