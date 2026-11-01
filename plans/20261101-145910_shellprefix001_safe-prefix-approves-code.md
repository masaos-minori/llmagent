## Goal
- Auto-approve `shell_run` only for command shapes that are read-only by construction, so that interpreters (`python`, `pytest`, `uv run`) and mutating git subcommands (`git branch -D`, `git diff --output=<file>`, ...) no longer bypass the high-risk human-in-the-loop prompt merely because their executable basename matches an entry in `approval_shell_safe_prefixes`.

## Priority
High

## Scope
- **In-Scope**:
  - Tighten the `shell_run` safe-prefix path in `scripts/agent/tool_policy.py` so an executable is auto-approved only when it has a defined read-only-by-construction rule and the parsed argument vector matches it; anything else is `high`.
  - Remove interpreters and test runners (`python`, `pytest`, `uv run`) from every auto-approved set so they follow the normal `shell_run = high` path.
  - Restrict `git` to read-only subcommands/flags; reject destructive forms (`branch -D/-m`, `checkout`, `push`, `diff --output=<file>`, ...).
  - Resolve the executable identity once and use the same normalized name for both the prefix match and the flag-denylist lookup.
  - Update `config/agent.toml` (`approval_shell_safe_prefixes` and its comment) to match the new policy and align with the shell server allowlist.
  - Update the two documents that describe this behavior.
  - Add regression tests using the shipped configuration values.
- **Out-of-Scope**:
  - The sandbox, the shell MCP server command allowlist, and `shell_cwd_allowed_dirs` (server allowlist is a read-only reference).
  - Parsing of `--flag=value` and generalizing the flag denylist to more executables — tracked in `issues/20261003-180337_shellrisk001_shell-risk-check-misses-flag-paths.md`; this issue changes only the executable-name normalization in `_unsafe_flag_denylist`, not its `--flag=value` coverage.
  - Risk classification of tools other than `shell_run`.
  - Any change to the protected-path / `allowed_root` checks.
- **Dependencies**:
  - `issues/20261003-180337_shellrisk001_shell-risk-check-misses-flag-paths.md` (open, no Plan yet): both touch `_check_positional_args` and `_unsafe_flag_denylist`. This issue defines the prefix policy first and stays within executable-name normalization; its tests must be reconciled with shellrisk001 when that issue is implemented. Non-blocking for this Plan.

## Background
`shell_run` has base risk `high`, but a command whose executable matches `approval_shell_safe_prefixes` is lowered to `none` and runs without a prompt. The shipped list contains `python`, `pytest`, `uv run`, and `git branch`. The match looks only at the executable (and subcommand) name, so `python -c <code>`, `pytest -p <plugin>`, `uv run <anything>`, `git branch -D <name>`, and `git diff --output=<file>` are auto-approved with arbitrary arguments whenever the positional-path check passes.

Verified against current source (`scripts/agent/tool_policy.py`):
- `_special_case_risk` (L221-260) handles `shell_run`: metacharacter → `high`; parse failure / empty argv → `high`; otherwise `_match_executable_identity(argv, cfg.approval.approval_shell_safe_prefixes)` returns `RiskLevel.NONE` on a bare basename/prefix match, then `_check_positional_args` and `_unsafe_flag_denylist` run. This override replaces the base `shell_run = high`.
- `_match_executable_identity` (L129-151) returns `NONE` purely from a name match — it inspects no argument beyond the leading tokens.
- `_check_positional_args` (L154-179) escalates only on a protected path or a path outside `allowed_root`; a code string or branch name passed positionally is treated as a path, and relative paths resolve against the agent process cwd.
- `_unsafe_flag_denylist` (L182-187) knows flags only for `find`, `cat`, `grep` (`_UNSAFE_FLAGS`, L44-48) and is called with the raw `argv[0]` (L256), while the prefix match uses `os.path.basename(argv[0])` — the two names disagree.
- Reproduction (no command executed): with the agent cwd inside a temp `allowed_root`, `python -c "__import__('shutil').rmtree('data')"`, `git branch -D feature`, `git diff --output=report.txt`, `pytest -p some_plugin`, and `uv run python build.py` all returned `none`; outside `allowed_root` the first two returned `high`, so the outcome depends on cwd.
- Existing tests (`TestPrefixCollision`, `tests/agent/test_tool_policy.py` L464+) validate the matching *mechanism* (basename, token boundary, quoting, metacharacters) with synthetic prefixes (`cat`, `git log`, `ls`, `echo`, `diff`, `c`, `./cat`, ...); none asserts argument-level safety on the shipped `python`/`pytest`/`uv run`/`git branch`/`find` values. 197 tests pass.

## Problem
The model can run arbitrary Python, import repository code via a test runner, delete or rename git branches, or write a diff to an arbitrary file inside the sandbox without the user seeing or approving the command. The human-in-the-loop guarantee for a `high` tool is bypassed by a name match. Also observed: `/usr/bin/find . -delete` returned `none` even though `-delete` is denylisted, because the denylist is looked up with the unnormalized first token while the prefix match uses the basename.

## Reason for Change
Auto-approval removes the only interactive check on `shell_run`. A prefix name does not describe what a command does: interpreters execute their argument, test runners import repository code, and `git branch` can delete or rename branches. The shipped configuration makes this reachable by default.

## Implementation Intent
Auto-approve only command shapes that are read-only by construction, expressed as an explicit, deny-by-default rule per executable (allowed subcommands and flags, no free-form code argument). Move interpreters and test runners out of the auto-approved set so they follow the normal high-risk prompt, or require an explicit operator opt-in with the risk stated in the configuration comments. Resolve the executable name once and use the same normalized name for matching and for the flag checks.

## Requirements
- `REQ-006`: Auto-approve `shell_run` only for command shapes that are read-only by construction. In `_special_case_risk`/`_match_executable_identity`, after the metacharacter and parse-fail fail-closed checks, an executable is auto-approved (`none`) only if it has a defined safe-shape rule and the parsed argv matches that rule; any executable without such a rule, or whose argv does not match, returns `high`. Remove `python`, `pytest`, and `uv run` from every auto-approved set so they fall through to the normal `shell_run = high` path. (`scripts/agent/tool_policy.py`; checked in Step 3)
- `REQ-007`: Give each retained executable an explicit allowed-subcommands/flags rule (deny by default). For `git`, allow only read-only subcommands (`log`, `status`, `show`, `diff` without an output-to-file flag, `branch` in list-only forms); reject mutating forms (`branch -D/-m`, `checkout`, `push`, `diff --output=<file>`, ...). Generalize the current `_UNSAFE_FLAGS` (find/cat/grep only) into this per-executable rule rather than a flag-only denylist. (`scripts/agent/tool_policy.py`; checked in Step 3)
- `REQ-008`: Resolve the executable identity once (basename of `argv[0]`) and thread that single normalized name through both the prefix match and the flag-denylist lookup, so `_unsafe_flag_denylist` is called with the same name the prefix match used. (`scripts/agent/tool_policy.py`; checked in Step 3)
- `REQ-009`: Update `approval_shell_safe_prefixes` in `config/agent.toml` to remove the interpreter/mutating entries (`python`, `pytest`, `uv run`, bare `git branch`) and align the remaining list with the shell server allowlist where they overlap; update the field comment to state that only read-only-by-construction command shapes are auto-approved and interpreters/test runners always prompt. Keep the edit within `ProductionConfigValidator` constraints. (`config/agent.toml`; checked in Step 3)
- `REQ-010`: Update `docs/23_agent/agent_06_02...md` (approval risk table) and `docs/91_security/security_02...md` to state which `shell_run` command shapes are auto-approved, why (read-only by construction), and that interpreters and test runners always prompt; describe intent and boundaries only, not the full prefix list. (located via `docs/00_index.md` "Document References by Task"; checked in Step 3)
- `REQ-011`: Add unit tests of `classify_risk` for `shell_run` using the shipped config values, in a working directory inside and outside `allowed_root`: each reproduction command (`python -c ...`, `pytest -p ...`, `uv run ...`, `git branch -D ...`, `git diff --output=...`) is at least `medium` (`high` for code execution and branch deletion); read-only git forms stay `none`; a test asserts the shared executable-name behavior for a full-path unsafe flag (`/usr/bin/find -delete` → `high`). Existing `TestPrefixCollision` tests keep passing. (`tests/agent/test_tool_policy.py`; checked in Step 3)

## Implementation Target Files
**Freeze status**: Frozen (set on 20261101-145910 after Step 8b: every row is
`Verified` and all four freeze criteria plus the additional checks pass).
Implementation Target Files Validation passes — see `rules/workflow-lifecycle.md`
Implementation Target Files Validation (Plan Freeze)).

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/tool_policy.py` | Modify `_match_executable_identity` / `_special_case_risk` / `_unsafe_flag_denylist`: per-executable safe-shape rule (deny by default), remove interpreters from auto-approval, normalize executable name once | `_match_executable_identity` (L129-151) returns `NONE` on a bare prefix match and inspects no argument; `_special_case_risk` L256 calls `_unsafe_flag_denylist(argv[0], ...)` with the raw token while the prefix match uses `os.path.basename(argv[0])`; `_UNSAFE_FLAGS` (L44-48) lists only find/cat/grep | REQ-006, REQ-007, REQ-008 / AC-1, AC-2, AC-3 | `_match_executable_identity` L129-151, `_special_case_risk` L249-258, `_unsafe_flag_denylist` L182-187 (checked in Step 3) | `tests/agent/test_tool_policy.py` | Verified |
| `config/agent.toml` | Modify `approval_shell_safe_prefixes` entry and its comment: remove python/pytest/uv run/bare `git branch`, align remaining with server allowlist, document read-only-by-construction intent | shipped list (L120-135) contains `python`, `pytest`, `uv run`, `git branch` and a comment that describes prefix auto-approval without listing safe shapes | REQ-009 / AC-1 | `config/agent.toml` L120-135 (checked in Step 3) | `tests/agent/test_tool_policy.py` | Verified |
| `tests/agent/test_tool_policy.py` | Add regression tests using shipped values; keep `TestPrefixCollision` passing | `TestPrefixCollision` (L464+) tests the matching mechanism with synthetic prefixes; no test asserts argument-level safety on shipped python/pytest/uv/git-branch/find values | REQ-011 / AC-1, AC-2, AC-3, AC-5 | `TestPrefixCollision` L464-733; 197 tests pass at HEAD (checked in Step 3) | itself | Verified |
| `docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md` | Document which `shell_run` shapes are auto-approved and why (via `docs/00_index.md` task mapping) | approval risk table (L78) states "`shell_run` ... starts with any of `approval_shell_safe_prefixes` → `none`" without defining which shapes count | REQ-010 / AC-4 | `agent_06_02...md` L78 (checked in Step 3) | docs checkers | Verified |
| `docs/91_security/security_02_high-risk-tool-common-policy.md` | Document intent and boundaries of shell auto-approval | security doc (L176) references `approval_shell_safe_prefixes` but does not list safe command shapes | REQ-010 / AC-4 | `security_02...md` L176 (checked in Step 3) | docs checkers | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan
Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file
  group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT
  appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as
  its own row when it requires modification — do not fold it into the row for the
  source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be
  `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `config/shell_mcp_server.toml` | Server allowlist (`pytest`, `python`, `python3`, `git`, `ruff`, `mypy`, basename-matched) — the alignment target for `approval_shell_safe_prefixes` | `config/agent.toml` / `REQ-009` |
| `issues/20261003-180337_shellrisk001_shell-risk-check-misses-flag-paths.md` | Sibling issue sharing `_check_positional_args`/`_unsafe_flag_denylist`; defines the `--flag=value` scope this issue must not touch | `scripts/agent/tool_policy.py` / `REQ-007`, `REQ-008` |
| `scripts/agent/tool_enums.py` | `RiskLevel` members (`none`/`medium`/`high`) and their meaning in the approval path | `scripts/agent/tool_policy.py` / `REQ-006` |

## Acceptance Criteria
- `AC-1` (`REQ-006`, `REQ-009`): `python -c ...`, `pytest ...`, `uv run ...`, `git branch -D ...`, and `git diff --output=...` are not auto-approved, regardless of the agent's working directory.
- `AC-2` (`REQ-007`): Read-only forms of `git status`, `git log`, `git diff`, and `git show` remain auto-approved (`none`).
- `AC-3` (`REQ-008`): The prefix match and the flag denylist use the same executable name (`/usr/bin/find -delete` → `high`).
- `AC-4` (`REQ-010`): The two documents list which command shapes are auto-approved and why, and state that interpreters and test runners always prompt.
- `AC-5` (`REQ-011`): The new tests fail on the current code and pass after the change; the existing suite (197 tests) still passes.

## Tests
- `AC-1` (`REQ-006`, `REQ-009`): `classify_risk(cfg, "shell_run", {command})` for each reproduction command is `high` (code execution, branch deletion) or at least `medium` (test runner, `uv run`, `git diff --output`), both inside and outside `allowed_root`, using the shipped `approval_shell_safe_prefixes`.
- `AC-2` (`REQ-007`): `git status`, `git log --oneline`, `git diff`, `git show`, and list-only `git branch` return `none` with the shipped config.
- `AC-3` (`REQ-008`): `/usr/bin/find -delete` returns `high`; a full-path read-only form (e.g. `/usr/bin/git log --oneline`) still returns `none`.
- `AC-5` (`REQ-011`): the full `tests/agent/test_tool_policy.py` suite passes, including every existing `TestPrefixCollision` case.

## Documentation Impact
`docs/*.md` must be updated (driven by `REQ-010`). Target the approval-risk-table doc for `shell_run` and the high-risk tool policy doc, located through `docs/00_index.md`'s "Document References by Task" table (do not hardcode filenames, they change as docs are split):
- the agent approval doc's `shell_run` row — add which command shapes are auto-approved and that interpreters/test runners always prompt;
- the security policy doc's shell bullet — describe intent and boundaries only, not the full prefix list.

## Assumptions
- **A1**: Interpreters and test runners must be removed from auto-approval. Derived from the Issue's explicit Acceptance Criteria and Reason for Change, not an owner decision.
- **A2**: This issue's change to `_unsafe_flag_denylist` is scoped to executable-name normalization only (`REQ-008`); the broader `--flag=value` generalization belongs to shellrisk001 and is not in scope here.
- **A3**: `cat`, `echo`, `ls`, `grep`, and read-only `git` remain auto-approved for read-only-by-construction operations; write redirections are already rejected by the metacharacter check, so existing `TestPrefixCollision` cases using these synthetic prefixes keep passing.
- **A4**: The per-executable safe-shape rule is defined in code, not via a new config key, so no new config schema/validation surface is introduced.
- **A5**: shellrisk001 has no Frozen Plan yet, so there is no Step 8b conflict to resolve now; it is recorded as a non-blocking sequencing dependency and reconciled when that issue is implemented.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether `python`, `pytest`, `uv run`, and `git branch` were accepted deliberately as safe | Documents describe prefix auto-approval but do not list safe commands | Issue Acceptance Criteria explicitly require these to be non-auto-approved, so the intent is settled; owner confirmation only needed to *re-add* them later | False |
| UNK-02 | The agent's working directory in production relative to `allowed_root` | Not shown by current evidence | Fix is cwd-independent (`AC-1` asserts both inside and outside `allowed_root`) | False |
| UNK-03 | What the sandbox allows (filesystem writes, network) | Sandbox scope was not reviewed in this issue | Out of scope; sandbox limits blast radius, and the fix removes the auto-approval regardless | False |
| UNK-04 | How the shell server matches its allowlist (basename of first token) | Server matching code was not read | Read-only reference; does not affect the agent-side fix | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/agent/tool_policy.py` | Modify | Medium (scoped to `shell_run` special-case path; other tools unaffected) | 2 | N/A (`git-fame` unavailable) | not applicable (rsynced) |
| `config/agent.toml` | Modify | Medium (shipped config read at startup; affects all `shell_run` auto-approval) | 10 | N/A (`git-fame` unavailable) | not applicable (rsynced) |
| `tests/agent/test_tool_policy.py` | Modify | Low (tests only) | 2 | N/A (`git-fame` unavailable) | not applicable (rsynced) |
| `docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md` | Modify | Low (docs only) | 12 | N/A (`git-fame` unavailable) | not applicable (rsynced) |
| `docs/91_security/security_02_high-risk-tool-common-policy.md` | Modify | Low (docs only) | 19 | N/A (`git-fame` unavailable) | not applicable (rsynced) |

## Design
This Issue leaves a design choice open (how to structure the per-executable rule), so
`skills/python-design/SKILL.md` was applied narrowly to its Step 4 decision entries and
Step 8 risks for this decision only.

**DD-1 — Structure of the per-executable auto-approval rule.** Three options:
- **Option A — full-command identity match (exact whitelist of complete command shapes).** Precise, but requires enumerating every allowed shape; breaks ~50 existing `TestPrefixCollision` tests that assert `none` for open-ended forms (e.g. `cat *.txt`, `echo --arg=...`, `git log --oneline`). Rejected.
- **Option B — prefix match + per-executable argument rule (generalize `_UNSAFE_FLAGS`).** Keep the basename/prefix gate, then apply a per-executable safe-shape rule (deny by default): defined allowed subcommands/flags per executable, and interpreters removed from the approved set entirely. Preserves existing tests (they use `cat`/`echo`/`ls`/`git log` synthetic prefixes that remain read-only-safe) and fixes the root cause (name match ≠ behavior). **Selected.**
- **Option C — remove risky prefixes from config only, no code change.** Leaves the prefix-only matching mechanism intact, so any future operator re-adding `python` reintroduces the bug; does not fix the root cause. Rejected as insufficient.

Rationale: Option B satisfies the Issue's "deny-by-default rule per executable; anything outside it is high" intent while keeping the change within the per-step revertibility bound and preserving existing coverage. Interpreters are excluded under Option B because no argument rule can make an interpreter read-only by construction (it executes its argument) — this follows from the Issue, not from the option choice.

**D1 — Requirement-ID offset.** Requirement IDs are scoped per Plan, but `tool_policy.py`
and `test_tool_policy.py` already carry inline annotations labeled `REQ-001`..`REQ-005`
for the already-implemented matching-mechanism requirements. This Plan uses
`REQ-006`..`REQ-011` for the argument-level safety requirements to avoid traceability
ambiguity between the two concerns.

**D2 — Interpreter removal is mandated, not an open decision.** The Issue's Acceptance
Criteria require `python -c ...`, `pytest ...`, `uv run ...` to be non-auto-approved, so
removing them is not an owner decision and is not a blocking Unknown.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above — do not restate file-level detail
independently of that frozen table. A step is a top-level numbered item (a Phase); its
checklist items are sub-tasks, and the Execution Status table has one row per step.

1. **Phase 1: Failing-test baseline**
   - [ ] Add the `REQ-011` regression tests to `tests/agent/test_tool_policy.py` using the shipped config values (cwd inside and outside `allowed_root`); confirm they FAIL on current code and record the failures as the baseline. No source change yet. (`tests/agent/test_tool_policy.py`; `REQ-011`)
2. **Phase 2: Core logic implementation**
   - [ ] Resolve the executable name once as `os.path.basename(argv[0])` inside `_special_case_risk`. (`scripts/agent/tool_policy.py`; `REQ-008`)
   - [ ] Replace the bare prefix match with a per-executable safe-shape rule (deny by default); interpreters (`python`, `pytest`, `uv run`) have no rule and fall through to `high`. (`scripts/agent/tool_policy.py`; `REQ-006`, `REQ-007`)
   - [ ] Define `git` read-only subcommands/flags; reject destructive forms. (`scripts/agent/tool_policy.py`; `REQ-007`)
   - [ ] Thread the single normalized executable name into `_unsafe_flag_denylist`; preserve every fail-closed branch (metachar, parse failure, empty argv, protected-path, `allowed_root`). (`scripts/agent/tool_policy.py`; `REQ-006`–`REQ-008`)
3. **Phase 3: Config change**
   - [ ] Edit `config/agent.toml`: remove `python`, `pytest`, `uv run`, bare `git branch`; align remaining with the server allowlist; update the field comment. (`config/agent.toml`; `REQ-009`)
   - [ ] Run config validation after the edit to confirm `ProductionConfigValidator` still passes. (`config/agent.toml`; `REQ-009`)
4. **Phase 4: Verification**
   - [ ] Run `tests/agent/test_tool_policy.py` (all green, incl. `TestPrefixCollision`), then `ruff` and `mypy --no-namespace-packages` on touched files, plus the config test suite. (`scripts/agent/tool_policy.py`, `tests/agent/test_tool_policy.py`; `AC-1`, `AC-2`, `AC-3`, `AC-5`)
5. **Phase 5: Documentation**
   - [ ] Update the two docs to describe which shapes are auto-approved and why; run the docs checkers. (`docs/23_agent/agent_06_02...md`, `docs/91_security/security_02...md`; `REQ-010`, `AC-4`)
6. **Phase 6: Deployment hand-off**
   - [ ] Commit and push via `git-commit-and-sync`. Deploying is the user's decision behind an approval gate; after deploy, verify the deployed `config/agent.toml` reflects the change. (`config/agent.toml`; `REQ-009`)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/tool_policy.py` | Unit: `classify_risk` for `shell_run` on reproduction and read-only commands, inside/outside `allowed_root` | `uv run pytest tests/agent/test_tool_policy.py` | reproduction → `high`/`medium`; read-only git → `none`; `/usr/bin/find -delete` → `high` |
| `config/agent.toml` | Config validity | config validation (per `rules/toolchain.md`) | `ProductionConfigValidator` passes |
| `tests/agent/test_tool_policy.py` | Regression (whole suite) | `uv run pytest tests/agent/test_tool_policy.py` | 197+ tests pass, incl. `TestPrefixCollision` |
| `scripts/agent/tool_policy.py`, `tests/agent/test_tool_policy.py` | Static checks | `uv run ruff` and `uv run mypy --no-namespace-packages` | clean on touched files |
| `docs/23_agent/agent_06_02...md`, `docs/91_security/security_02...md` | Docs checker | docs checker per `rules/toolchain.md` | pass |

## Risks
- **Risk**: Tightening the rule breaks many existing tests that currently assert `none` for open-ended safe forms. → **Mitigation**: preserve read-only-by-construction shapes for `cat`/`echo`/`ls`/`grep`/read-only `git`; existing `TestPrefixCollision` cases use these synthetic prefixes and keep passing; new behavior only affects `python`/`pytest`/`uv run`/`git branch`/`find`, which have no existing `none` assertions.
- **Risk**: The per-executable rule is too narrow and breaks legitimate read-only workflows. → **Mitigation**: keep the shipped read-only entries auto-approved; document the shapes; the owner can widen via the config comment.
- **Risk**: Coordination with shellrisk001 on `_unsafe_flag_denylist`/`_check_positional_args`. → **Mitigation**: this issue changes only the executable-name normalization in `_unsafe_flag_denylist` and does not touch `_check_positional_args`'s `--flag=value` parsing (shellrisk001's scope); reconcile tests when shellrisk001 is implemented.
- **Risk**: The `config/agent.toml` edit fails `ProductionConfigValidator`. → **Mitigation**: run config validation after the edit (`Phase 3`); keep `approval_shell_safe_prefixes` a valid list.
- **Risk**: `radon` grades `_special_case_risk` C(13) and `classify_risk` C(13); adding a per-executable rule raises complexity. → **Mitigation**: keep the rule table data-driven and the matching helper small; re-run `radon` in `Phase 4` and confirm no new blocker-grade function.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Failing-test baseline (`tests/agent/test_tool_policy.py`, shipped values) | Pending | — | — | |
| 2 | Core logic in `scripts/agent/tool_policy.py` (per-executable rule, interpreter removal, executable-name normalization) | Pending | — | — | |
| 3 | `config/agent.toml` edit + config validation | Pending | — | — | |
| 4 | Verification: suite, ruff, mypy | Pending | — | — | |
| 5 | Docs update + docs checkers | Pending | — | — | |
| 6 | Deployment hand-off (commit/push; deploy is user decision) | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261101-073644_shellprefix001_safe-prefix-approves-code.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261101-145910
- **Related target files**: `scripts/agent/tool_policy.py`, `config/agent.toml`, `tests/agent/test_tool_policy.py`, `docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md`, `docs/91_security/security_02_high-risk-tool-common-policy.md` — the full list of `File Path` values from `Implementation Target Files` above, once `Frozen`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-006 | Required Changes 1; Implementation Intent; Acceptance Criteria 1 | `scripts/agent/tool_policy.py` | Phase 2 | AC-1 | `classify_risk` reproduction tests | Confirmed by repository evidence |
| REQ-007 | Required Changes 1-2; Acceptance Criteria 2 | `scripts/agent/tool_policy.py` | Phase 2 | AC-2 | read-only git tests | Confirmed by repository evidence |
| REQ-008 | Required Changes 3; Background (`/usr/bin/find -delete`) | `scripts/agent/tool_policy.py` | Phase 2 | AC-3 | `/usr/bin/find -delete` test | Confirmed by repository evidence |
| REQ-009 | Required Changes 2; Constraints; Acceptance Criteria 1 | `config/agent.toml` | Phase 3 | AC-1 | config validation | Explicit in issue |
| REQ-010 | Documentation Impact; Acceptance Criteria 4 | `docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md` | Phase 5 | AC-4 | docs checker | Explicit in issue |
| REQ-010 | Documentation Impact; Acceptance Criteria 4 | `docs/91_security/security_02_high-risk-tool-common-policy.md` | Phase 5 | AC-4 | docs checker | Explicit in issue |
| REQ-011 | Testing Expectations; Acceptance Criteria 5 | `tests/agent/test_tool_policy.py` | Phase 1, Phase 4 | AC-1, AC-2, AC-3, AC-5 | whole suite | Explicit in issue |
