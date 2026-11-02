## Goal
- Make the `shell_run` safe-prefix path check in `scripts/agent/tool_policy.py` apply the same protected-path and `allowed_root` checks to the value of a long `--flag=value` token as it applies to a bare positional argument, so a path hidden inside `--flag=value` can no longer keep an auto-approved command at `RiskLevel.NONE`.

## Priority
Medium

## Scope
- **In-Scope**:
  - In `_check_positional_args()` (`scripts/agent/tool_policy.py`), extract the value part of a long `--flag=value` token and route it through the existing protected-path and `allowed_root` checks, unchanged in threshold and result (`RiskLevel.HIGH`).
  - Add tests for the new coverage and for the unchanged cases (`tests/agent/test_tool_policy.py`).
- **Out-of-Scope**:
  - Generalizing `_UNSAFE_FLAGS` beyond `find`/`cat`/`grep`, per-executable deny-by-default rules, normalizing the executable name for the denylist lookup, and removing `python`/`pytest`/`uv run`/`git branch` from auto-approval: all belong to `issues/20261101-073644_shellprefix001_safe-prefix-approves-code.md`.
  - The list-valued and non-listed path-argument gaps in `check_allowed_root`/`_escalate_for_path`: `issues/20261101-073742_pathkeys001_path-checks-skip-lists.md`.
  - `tool_approval.check_approval()`'s approval-prompt flow, the format of `approval_shell_safe_prefixes`, the risk thresholds, and the existing `find`/`cat`/`grep` unsafe-flag entries (Issue Constraints and Out of Scope).
  - Values attached to a short flag without a separator (`-c/etc/x`) and `key=value` operands that do not start with `-` (see UNK-02).
- **Dependencies**:
  - `issues/20261101-073644_shellprefix001_safe-prefix-approves-code.md` (open, still in `issues/`, High, no Plan yet): it changes the same functions (`_check_positional_args`, `_unsafe_flag_denylist`, `_special_case_risk`) and the same test file, and decides which commands are auto-approved at all. Its prefix policy should be decided and implemented first; this Plan's tests may then need reconciling (some `python`/`pytest` cases may become redundant, `git diff --output=...` is expected to leave auto-approval there). The two Issues can be sequenced without owner input; recorded as non-blocking UNK-01.
  - `issues/20261101-073742_pathkeys001_path-checks-skip-lists.md` (open, related, not a prerequisite): a different gap in the agent-side path policy in the same file (`check_allowed_root`, `_escalate_for_path`, `_iter_string_arg_values`); no shared function with this Plan.

## Background
`scripts/agent/tool_policy.py::_special_case_risk` lowers a `shell_run` command to `RiskLevel.NONE` (no prompt) when `_match_executable_identity` matches an `approval_shell_safe_prefixes` entry, after two guards: `_check_positional_args` (protected path or outside `allowed_root` gives HIGH) and `_unsafe_flag_denylist`. The shipped `config/agent.toml` has `approval_shell_safe_prefixes` = `ls`, `cat`, `echo`, `git log|status|diff|show|branch`, `pwd`, `find`, `grep`, `uv run`, `python`, `pytest`; `approval_protected_paths` = `/opt/`, `/etc/`, `/boot/`, `/usr/`, `/bin/`, `/sbin/`; `allowed_root` = `/opt/llm`. The shell MCP server's own allowlist (`config/shell_mcp_server.toml`, `command_allowlist`) is `pytest`, `python`, `python3`, `git`, `ruff`, `mypy` (basename match), so `cat`, `grep`, `find`, `ls` are probably rejected by the server and the reachable gap is mainly `python`, `pytest` and `git` (checked in Step 2; the server's matching code was not read, Needs confirmation, but it does not change this Plan's scope because the policy function is executable-agnostic).
`docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md` and `docs/91_security/security_02_high-risk-tool-common-policy.md` describe only the safe-prefix override ("`command` starts with any of `approval_shell_safe_prefixes` -> `none`"); neither describes token parsing or the positional/path checks (checked in Step 2). The "starts with" wording is stale relative to the current parsed-identity matching; refreshing it is a documentation matter for `shellprefix001`, not this Plan.

## Problem
`_check_positional_args()` builds `positional = [a for a in argv[1:] if not a.startswith("-")]` and checks only those tokens. A token such as `--rootdir=/etc` starts with `-`, so its value is never examined. Adversarial verification (Step 2, classification only through `classify_risk` with the real `config/agent.toml` values and a temporary `allowed_root`; no command executed) showed, with the agent working directory inside `allowed_root`:
- `git diff --output=/etc/x` -> none, while `git diff /etc/shadow` and `git diff --output /etc/x` -> high (the space-separated value is a positional token and is already checked).
- `pytest --rootdir=/etc`, `pytest --junitxml=/etc/out.xml`, `pytest --confcutdir=/tmp` -> none; `pytest --rootdir /etc` -> high.
- `cat --file=/etc/shadow`, `grep --file=/etc/shadow x`, `grep --include=/etc/shadow x`, `ls --ignore=/etc` -> none (these executables are probably unreachable through the server, but the policy function is shared).
- With the agent working directory outside `allowed_root`, `git diff --output=/etc/x` happens to be high only because the subcommand `diff` is itself resolved as a relative path outside the root; `pytest --rootdir=/etc` stays none because there is no positional token. The bypass therefore depends on `allowed_root` being set, the agent's working directory, and whether another positional token exists.
Correction to the Issue: the Issue's wording "flag-value path extraction" suggests space-separated flag values are also missed; they are not, since the value is a non-dash token and is already treated as positional. The uncovered forms are `--flag=value` (in scope) and short flags with an attached value such as `-c/etc/x.ini` or `-I/etc` (not named in the Required Changes; UNK-02).

## Reason for Change
`approval_shell_safe_prefixes` removes the only interactive check on `shell_run`. The protected-path and `allowed_root` guard in `_check_positional_args` is meant to keep commands that touch protected locations at HIGH; a path supplied as `--flag=value` bypasses that guard and can leave the command auto-approved. Closing the `--flag=value` form is a small fail-closed extension that does not depend on the broader prefix-policy redesign.

## Implementation Intent
Before the positional check, derive from each `argv[1:]` token the string that should be treated as a path candidate: a bare token as before, and for a token that starts with `--` and contains `=`, the text after the first `=`. Candidates then go through the existing loop (protected prefix, then `allowed_root` resolution with the `ValueError`/`OSError` fail-closed branch). Bare flags (`--help`), the `--` separator, short flags (`-la`) and empty values (`--flag=`) contribute no candidate. Thresholds, the early return for a HIGH base, and the return value for a clean command stay as they are. The result can only escalate, never lower, a risk.

## Requirements
- `REQ-001`: `_check_positional_args()` MUST treat the value after the first `=` of a long `--flag=value` token as a path candidate and apply the same protected-path and `allowed_root` checks (result `RiskLevel.HIGH`) as for a bare positional token; a bare `--flag`, `--`, a short flag, and `--flag=` with an empty value MUST contribute no candidate.
- `REQ-002`: Existing behavior MUST be unchanged: bare positional tokens are checked as before, a command whose tokens are all clean flags or safe paths still returns `None` (so the command stays `RiskLevel.NONE`), the HIGH-base early return, the `ValueError`/`OSError` branch and the `_UNSAFE_FLAGS` entries are untouched, and no escalation threshold changes.
- `REQ-003`: `tests/agent/test_tool_policy.py` MUST gain regression tests: a protected-path or outside-`allowed_root` value supplied as `--flag=value` escalates to high identically to the space-separated form (using `python`, `pytest` and `git diff`, the executables the server allowlist permits, plus one `cat`/`grep` case because the policy is executable-agnostic); an in-root `--flag=value`, a non-path value (`--since=yesterday`), a bare `--flag`, and `--flag=` stay `none`; a `--flag=value` with a NUL character escalates through the fail-closed branch.

## Implementation Target Files
**Freeze status**: Frozen

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/agent/tool_policy.py | Extract the value of `--flag=value` tokens as path candidates in `_check_positional_args()` | The `not a.startswith("-")` filter drops the whole token, so its value is never checked | REQ-001, REQ-002; AC-1, AC-2 | `_check_positional_args` builds `positional` from tokens not starting with `-`; classification of `git diff --output=/etc/x` and `pytest --rootdir=/etc` returned `none` while the space-separated forms returned `high` (checked in Step 2 and Step 3) | `tests/agent/test_tool_policy.py` | Verified |
| tests/agent/test_tool_policy.py | Add `--flag=value` regression tests next to the existing `shell_run` positional-argument tests | No existing test covers a `--flag=value` path; existing tests (`test_cat_protected_path_escalates`, `test_cat_outside_allowed_root_escalates`, `test_flag_only_no_positional_routing_needed`, `test_positional_arg_value_error_in_resolve_escalates` and their `prefix_collision` twins) cover only bare tokens | REQ-003; AC-3, AC-4 | The file builds configs with `_cfg(approval_shell_safe_prefixes=..., allowed_root=..., approval_protected_paths=...)` and asserts `classify_risk(...) == "high"/"none"` (checked in Step 3) | tests/agent/test_tool_policy.py | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| config/agent.toml | Shipped `approval_shell_safe_prefixes`, `approval_protected_paths` (`/opt/` etc.), `allowed_root` (`/opt/llm`), `shell_run` risk rule; tests must be consistent with these values | REQ-003 |
| config/shell_mcp_server.toml | `command_allowlist` (`pytest`, `python`, `python3`, `git`, `ruff`, `mypy`) decides which executables tests should use as reachable examples | REQ-003 |
| docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md | Documents the safe-prefix override and risk escalation; confirms nothing documents token-parsing coverage | Documentation Impact |
| docs/91_security/security_02_high-risk-tool-common-policy.md | Security-policy statement on safe-prefix auto-approval; confirms no token-parsing statement | Documentation Impact |
| issues/20261101-073644_shellprefix001_safe-prefix-approves-code.md | Overlapping Issue (same functions and test file) with a Frozen Plan (`plans/20261101-145910_...`, verified 20261103); defines the ordering dependency | Scope Dependencies, UNK-01 |
| issues/20261101-073742_pathkeys001_path-checks-skip-lists.md | Open related Issue in the same module; confirms no shared function | Scope Dependencies |

## Acceptance Criteria
- AC-1 (REQ-001): `classify_risk` for a `shell_run` command with a safe prefix and a `--flag=value` whose value is under an `approval_protected_paths` entry or outside `allowed_root` returns `high`, the same as the equivalent space-separated command.
- AC-2 (REQ-002): All existing `shell_run` risk-classification tests in `tests/agent/test_tool_policy.py` pass unchanged; bare positional behavior, `_UNSAFE_FLAGS` entries and thresholds are unchanged.
- AC-3 (REQ-003): New tests cover the escalation, parity-with-space-separated, in-root, non-path value, bare flag, empty value and NUL-value cases, and the escalation tests fail on the pre-change code.
- AC-4 (REQ-001, REQ-003): No new test executes a command; tests only call `classify_risk`.

## Tests
- (REQ-001, REQ-003) For prefixes `python`, `pytest`, `git diff` and one `cat`/`grep` case: `--flag=/etc/...` with a protected path configured, and `--flag=<path outside allowed_root>` with `allowed_root` set, each return `high`; the same path as a separate token returns `high` (parity assertion).
- (REQ-002, REQ-003) `--flag=<path under allowed_root>` returns `none`; `--since=yesterday` (relative non-path value, resolves under the root) returns `none`; `--help`/`-la` and `--flag=` return `none`; `--flag=\x00bad` returns `high`.
- (REQ-002) Run the full `tests/agent/test_tool_policy.py` to confirm the existing cases pass.
- Tests set `allowed_root` and the working directory explicitly (for relative-value cases `monkeypatch.chdir` into a temporary directory), because `Path(...).resolve()` depends on the process working directory.

## Documentation Impact
N/A: no documentation describes token-parsing coverage of this check (checked in Step 2: `docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md` and `docs/91_security/security_02_high-risk-tool-common-policy.md` describe only the safe-prefix override). The stale "starts with" wording in the former is a `shellprefix001` documentation matter.

## Assumptions
- A `--flag=value` value is treated as a path candidate even when it is not a path (for example `--since=yesterday`), exactly as bare positional tokens already are (a code string or branch name is treated as a path today). Because a relative value resolves against the agent's working directory, it escalates only when the directory is outside `allowed_root` (when a positional subcommand token already escalates) or the value is absolute/traversing outside the root or under a protected prefix. This extension only adds HIGH escalations; it does not lower any risk. Falsifiable by the Tests above.
- Only values after a `--` prefixed long flag are extracted; a short flag with an attached value is out of scope (UNK-02), consistent with the Issue's Required Changes.
- In the shipped configuration, `approval_protected_paths` contains `/opt/` while `allowed_root` is `/opt/llm`, so an absolute value under `/opt/llm` escalates through the protected prefix just as a bare positional path does today; this Plan preserves that parity and does not change it.
- Ordering against `shellprefix001`: that Issue is decided and implemented first; this Plan's implementation procedure re-reads `_check_positional_args` and the `shell_run` tests at that time, and reconciles tests that `shellprefix001` makes redundant. Judged a sequencing dependency, not a design conflict, because this Plan changes only candidate extraction inside `_check_positional_args` and `shellprefix001` changes which commands reach it.
- Overlap with other Frozen Plans (re-verified 20261103): `shellprefix001` now has a Frozen Plan (`plans/20261101-145910_shellprefix001_safe-prefix-approves-code.md`) sharing this Plan's two target files; judged the same sequencing dependency (that Plan first), not a design conflict — its scope changes `_match_executable_identity`/`_special_case_risk`/`_unsafe_flag_denylist` and it explicitly does not touch `_check_positional_args` (that Plan's A2 and Risks).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|----|---|---|---|---|
| UNK-01 | ~~Whether `shellprefix001`'s redesign of `_special_case_risk`/`_check_positional_args` keeps the `_check_positional_args(cfg, argv, base)` shape, so that this Plan's change and tests still apply as written~~ Resolved 20261103: the Frozen Plan `plans/20261101-145910_shellprefix001_safe-prefix-approves-code.md` changes only `_match_executable_identity`/`_special_case_risk`/`_unsafe_flag_denylist`, states it does not touch `_check_positional_args` (its A2, Risks), and keeps the call `_check_positional_args(cfg, argv, match)` in `_special_case_risk` (L249-258); the function shape this Plan assumes is preserved | `shellprefix001`'s intended function shapes (now documented in its Frozen Plan) | Resolved by cross-plan evidence; re-verify the function body at implementation time before editing (sequencing dependency) | False |
| UNK-02 | Whether the owner wants attached short-flag values (`-c/etc/x.ini`, `-I/etc`) and `key=value` operands (`-X pycache_prefix=/etc/x`) covered by the same extraction. Observed: `pytest -c/etc/x.ini` and `ls -I/etc` classify as `none` | The Issue names only `--flag=value`; which short flags take attached values is per executable and was not enumerated | Owner decision; if wanted, file a follow-up Issue (it needs per-executable flag knowledge, which overlaps `shellprefix001`) | False |
| UNK-03 | Whether the shell MCP server rejects `cat`, `grep`, `find`, `ls` (not in `command_allowlist`) so the agent-side entries are unreachable (Needs confirmation: the server's matching code was not read) | Server command-matching code not inspected | Verified by `shellprefix001` (it lists the same Needs confirmation); does not change this Plan's scope | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/agent/tool_policy.py | Modify | Low: `_check_positional_args` is called only from `_special_case_risk` (`shell_run` safe-prefix path); the change only adds HIGH escalations | 2 commits | 1 author (Path A: no historical tooling) | not applicable (rsynced) |
| tests/agent/test_tool_policy.py | Modify | Low: test-only | 2 commits | 2 author-name spellings of one person (effectively 1) | not applicable (rsynced) |

## Design
- Path A: two target files, no public or runtime interface change (`_check_positional_args` is module-private; its signature stays), no schema change. Classified in Step 3; no reclassification at Step 5.
- Approach: build the candidate list in one small step ahead of the existing loop (or a tiny module-private helper in the same file) and keep the loop body, the protected-prefix check, the `allowed_root` check and the `ValueError`/`OSError` branch as they are. Extraction rule: token starts with `--` and contains `=` -> text after the first `=`; token not starting with `-` -> the token; everything else -> none. The empty-candidates early return must now test the candidate list, not the pre-extraction filter result.
- Alternatives considered: (1) scan every token containing `=` regardless of the leading dashes (rejected: would also treat operands such as `-X pycache_prefix=/etc/x` and `VAR=value`, whose semantics are per executable; deferred to UNK-02/`shellprefix001`); (2) per-executable flag tables of path-taking flags (rejected here: that is the deny-by-default redesign owned by `shellprefix001`).
- Complexity baseline (radon, Step 5): `_check_positional_args` C (11), `_special_case_risk` C (13), `_unsafe_flag_denylist` A (3); a helper keeps the former from growing. `vulture scripts/ --min-confidence 80` reports only two unrelated findings (`scripts/rag/ingestion/document_manager.py`, `scripts/shared/runtime_paths.py`); `bandit` reports nothing for `scripts/agent/tool_policy.py` (`uv run bandit`; the bare `bandit` binary is not on PATH).

## Implementation steps
1. **Phase 1: Core change**
   - [ ] Re-read `_check_positional_args` and `_special_case_risk` (UNK-01), then replace the `not a.startswith("-")` filter with candidate extraction that also yields the value of `--flag=value` tokens, keeping thresholds, the HIGH-base early return and the `ValueError`/`OSError` branch (REQ-001, REQ-002; scripts/agent/tool_policy.py).
2. **Phase 2: Tests**
   - [ ] Add the `--flag=value` regression tests described in Tests next to the existing shell-run positional-argument tests, and confirm the escalation tests fail against the unmodified function (REQ-003; tests/agent/test_tool_policy.py).
3. **Phase 3: Verification and deployment hand-off**
   - [ ] Run the Validation plan commands, including diff-cover without `--fail-under` first to record the baseline and then at the `rules/toolchain.md` threshold (REQ-001, REQ-002, REQ-003; scripts/agent/tool_policy.py, tests/agent/test_tool_policy.py).
   - [ ] Deploy is a hand-off to `skills/deploy/SKILL.md`: the change must be committed and pushed first, and deploying is the user's decision (approval gate); `scripts/agent/tool_policy.py` ships through the normal rsync with no new file, config key or service change (REQ-001; scripts/agent/tool_policy.py).

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/tool_policy.py, tests/agent/test_tool_policy.py | Unit | `uv run pytest tests/agent/test_tool_policy.py` | All existing and new tests pass (AC-1 to AC-4) |
| scripts/agent/tool_policy.py | Unit (regression) | `uv run pytest tests/agent -k "tool_policy or tool_approval"` | No regression in callers' classification tests (AC-2) |
| scripts/agent/tool_policy.py | Static | `uv run ruff check scripts/agent/tool_policy.py tests/agent/test_tool_policy.py` and `uv run mypy scripts/agent/tool_policy.py` | No findings |
| scripts/agent/tool_policy.py | Complexity / security | `radon cc scripts/agent/tool_policy.py -s`; `uv run bandit -r scripts/agent/tool_policy.py -c pyproject.toml` | `_check_positional_args` does not exceed its current rank C; no bandit findings |
| scripts/agent/tool_policy.py | Coverage | `rules/toolchain.md` section 7 diff-cover sequence | Changed lines meet the Completion checklist threshold |

## Risks
- **Risk**: A non-path `--flag=value` value (for example `--format=%H`, `--include=*.py`) is resolved as a path and escalates when the agent's working directory is outside `allowed_root` (likelihood: low; in that situation a positional subcommand token already escalates the same command) → **Mitigation**: the extension only adds HIGH (fail-closed, an extra prompt, never an auto-approval); tests pin the `--since=yesterday` and in-root cases so the behavior is explicit.
- **Risk**: `shellprefix001` rewrites the same functions and tests first, causing merge conflicts or redundant tests here (likelihood: medium; the Issue itself states the dependency) → **Mitigation**: Dependencies and UNK-01 fix the order (prefix policy first); the implementation procedure re-reads the current function, and the Plan is amended if the function shape changed.
- **Risk**: The fix gives a false sense that flag-borne paths are fully covered while attached short-flag values and `key=value` operands remain unchecked (likelihood: medium) → **Mitigation**: both are stated as Out-of-Scope and recorded as UNK-02; the auto-approval of interpreters that makes them dangerous is the subject of `shellprefix001`.
- **Risk**: Relative values resolve against the agent process's working directory, not the shell server's (`shell_cwd_allowed_dirs`), so a relative `--flag=../x` is judged against the wrong base (likelihood: low; the same limitation already applies to bare positional tokens) → **Mitigation**: parity with positional behavior is the requirement; the cwd mismatch is raised in `shellprefix001`'s Background and is not widened here.
- **Risk**: Tests that depend on the process working directory become flaky (likelihood: low) → **Mitigation**: set `allowed_root` and use `monkeypatch.chdir` into a temporary directory explicitly in every relative-value test.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Candidate extraction for `--flag=value` in `_check_positional_args` (scripts/agent/tool_policy.py) | In Progress | — | — | After `shellprefix001` (UNK-01) |
| 2 | Add `--flag=value` regression tests (tests/agent/test_tool_policy.py) | In Progress | — | — |  |
| 3 | Validation commands and deploy hand-off | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261103-073729_01_scripts_agent_tool_policy.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261103-073729_02_tests_agent_test_tool_policy.py.md` | 2 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261003-180337_shellrisk001_shell-risk-check-misses-flag-paths.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261101-142514
- **Related target files**: scripts/agent/tool_policy.py, tests/agent/test_tool_policy.py

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Problem, Required Changes (parse `--flag=value`); `_check_positional_args` `not a.startswith("-")` filter; classification of `git diff --output=/etc/x` and `pytest --rootdir=/etc` | scripts/agent/tool_policy.py | Step 1 | AC-1 | `uv run pytest tests/agent/test_tool_policy.py` (new escalation tests) | Confirmed by repository evidence |
| REQ-002 | Issue Constraints, Acceptance Criteria (existing behavior unchanged) | scripts/agent/tool_policy.py | Step 1 | AC-2 | Existing `shell_run` tests in `tests/agent/test_tool_policy.py` | Explicit in issue |
| REQ-003 | Issue Required Changes (add tests), Testing Expectations; reachable executables from `config/shell_mcp_server.toml` | tests/agent/test_tool_policy.py | Step 2 | AC-3, AC-4 | `uv run pytest tests/agent/test_tool_policy.py` | Explicit in issue |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261103-073729 -->