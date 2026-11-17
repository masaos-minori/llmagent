## Goal
Tighten the shell-mcp server command allowlist from a basename-only gate to a
per-command argument-shape contract, so an allowlisted interpreter (`python`,
`python3`) cannot run free-form code and `git` cannot run mutating subcommands
through `shell_run`. The basename allowlist stays the first gate; an argument
validation becomes the second, failing closed on any shape outside the contract.

## Priority
Medium

## Scope
- **In-Scope**:
  - Add a deny-by-default argument-shape contract keyed by executable basename,
    evaluated after the existing basename allowlist match in
    `ShellService._check_command`.
  - Ship a conservative initial contract: permit read-only `git` subcommands and
    static-analysis `ruff`/`mypy` flag shapes; fail closed for interpreter
    free-form code (`python -c ...`, `python3 -c ...`) and mutating `git`
    subcommands (`git branch -D`, `git push`, etc.).
  - Reject any executable or argument shape not explicitly permitted by the
    contract (fail closed); never execute before validation.
  - Update the `command_allowlist` comment in `config/shell_mcp_server.toml` to
    state which argument shapes are permitted per command and that
    code-executing/mutating forms are rejected.
  - Add unit tests of `_check_command` covering rejection of code-execution and
    mutating-git forms and allowance of safe forms. No subprocess is launched in
    tests.
- **Out-of-Scope**:
  - The agent-side `tool_policy.py` auto-approval layer (`shellprefix001`).
  - The sandbox, resource limits, and environment filtering.
  - Changing which commands appear in `command_allowlist`; entries stay as-is.
  - Routing code-executing forms to human-in-the-loop approval (agent-layer
    concern, out of scope).
- **Dependencies**: `N/A: none`
  - Sequencing note: related issue
    `issues/20261101-073644_shellprefix001_safe-prefix-approves-code.md` covers the
    agent-side layer and is archived (`issues/done/`); its plan
    `plans/done/20261101-145910_shellprefix001_safe-prefix-approves-code.md` is
    closed. This issue addresses the independent server layer it left out of
    scope; no open sequencing dependency blocks this Plan.

## Background
`ShellService._check_command` (`scripts/mcp_servers/shell/shell_service.py`) parses
the request into `argv` and accepts it when `os.path.basename(argv[0])` is in
`self._allowlist`; `argv[1:]` is returned to the runner unchecked. The allowlist is
built in `ShellService.__init__` by normalizing `policy.allowed_commands` to
basenames. `config/shell_mcp_server.toml` sets
`command_allowlist = ["pytest", "python", "python3", "git", "ruff", "mypy"]` with
the comment "permitted command names (matched against argv[0] basename)". ADR-014
makes the MCP server own the technical safety of shell execution (allowlist
enforcement, cwd/path validation, sandboxed execution, resource limits); this is
not duplicated in the Orchestrator/ToolExecutor layers.

## Problem
An allowlisted interpreter entry is functionally "execute any code": the allowlist
constrains the executable name only, not what the command does. `python -c
__import__('os').system('id')` and `pytest` importing repository code run arbitrary
code; `git branch -D feature` / `git push` delete or push branches. A caller
authenticated to `shell_run` reaches all of these because only `argv[0]` is checked.
A reviewer reading `command_allowlist` assumes the listed tools' behavior is
constrained; the comment documents argv[0]-only matching without stating that a
`python` entry means arbitrary code execution, so nothing alerts the operator.

## Reason for Change
The allowlist is the last technical safety boundary (ADR-014) before execution. A
basename-only match for interpreters and VCS tools degrades to "run whatever name
is allowlisted with any arguments," which defeats the least-privilege intent. The
gap is invisible in configuration because the comment documents argv[0]-only
matching without stating the impact of an interpreter entry.

## Implementation Intent
Add an argument-shape check to the server's command validation, immediately after
the existing basename allowlist gate. For each allowlisted executable, define the
permitted argument shapes as a deny-by-default contract: allowed subcommands/flags
and forbidden patterns such as a free-form code string for interpreters or
mutating git subcommands. Anything outside the per-command contract fails closed.
Keep the basename allowlist as the first gate; add argument validation as the
second. The contract is a module-level table keyed by basename so new executables
require an explicit decision. Do not change the agent-side `tool_policy` layer, the
sandbox, resource limits, or env filtering.

## Requirements
- `REQ-001`: After the basename allowlist match, `_check_command` validates `argv[1:]`
  against the per-command contract for each allowlisted command that has a contract entry;
  an argument shape outside a contract's permitted shapes fails closed with a domain
  exception before execution. A basename outside the basename allowlist fails closed at the
  first gate; an allowlisted command without a contract entry passes through unchanged.
- `REQ-002`: The shipped deny-by-default contract permits read-only `git` subcommands
  and static-analysis `ruff`/`mypy` flag shapes, and rejects interpreter free-form code
  (`python -c ...`, `python3 -c ...`) and mutating `git` subcommands (`git branch -D`,
  `git push`, etc.).
- `REQ-003`: The `command_allowlist` comment in `config/shell_mcp_server.toml` states
  which argument shapes are permitted per command and that code-executing/mutating forms
  are rejected; it states intent and boundaries without enumerating every flag.
- `REQ-004`: Unit tests assert code-execution and mutating-git forms are rejected and
  read-only/safe forms pass; no subprocess is launched (assert rejection before launch,
  or use `dry_run`).

## Implementation Target Files
**Freeze status**: Frozen (20261117-232635). Every `Implementation Target Files` row is
`Verified` and passes the Initial validation checks in
`rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan Freeze); no file
appears in both `Implementation Target Files` and `Reference Files`, and no row is a
directory, glob, component, or vague phrase. See `rules/workflow-lifecycle.md`
Implementation Target Files Validation (Plan Freeze).

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/mcp_servers/shell/shell_service.py` | Modify | Add a deny-by-default per-command argument-shape contract and call it from `_check_command` after the basename allowlist match; raise `ShellAuthorizationError` on a rejected shape. Module docstring already records ADR-014 ownership. | REQ-001, REQ-002 | `_check_command` compares only `os.path.basename(argv[0])` and returns `argv` unchecked (checked in Step 3); `ShellService.__init__` builds `self._allowlist` from `policy.allowed_commands` (checked in Step 3) | `tests/mcp_servers/shell/test_shell_mcp_service.py::TestCheckCommand` | Verified |
| `tests/mcp_servers/shell/test_shell_command_arg_contract.py` | Create | New file. Test module asserting the argument-shape contract: code-execution and mutating-git forms rejected, read-only/safe forms allowed, unrecognized shapes fail closed. | REQ-001, REQ-002, REQ-004 | Existing `TestCheckCommand` uses `_make_service` with `allowed_commands=frozenset(["ls", "echo"])` and calls `svc._check_command(req)`; `ls`/`echo` have no contract entry and pass through (checked in Step 3) | this module | Verified |
| `config/shell_mcp_server.toml` | Modify | Rewrite the `command_allowlist` comment to state permitted argument shapes per command and that code-executing/mutating forms are rejected. | REQ-003 | `command_allowlist = ["pytest", "python", "python3", "git", "ruff", "mypy"]` with an argv[0]-only-matching comment that omits interpreter impact (checked in Step 3) | none (config comment only) | Verified |

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
| `scripts/shared/protocols/shell.py` | `ShellPolicy` dataclass holds `allowed_commands`; confirms the allowlist source and that adding a field here would touch a shared runtime interface (avoided by a service-local contract). | `scripts/mcp_servers/shell/shell_service.py` / REQ-001 |
| `tests/mcp_servers/shell/test_shell_mcp_service.py` | Existing `TestCheckCommand` and `_make_service`/`_make_policy` fixtures show how `_check_command` is exercised without launching subprocesses; new assertions belong here or in the dedicated module. | `tests/mcp_servers/shell/test_shell_command_arg_contract.py` / REQ-004 |
| `scripts/mcp_servers/shell/shell_models.py` | `ShellRunRequest`/`ShellValidationError`/`ShellAuthorizationError` shapes and how `run_command` threads them. | `scripts/mcp_servers/shell/shell_service.py` / REQ-001 |

## Acceptance Criteria
- `python -c <code>` and `python3 -c <code>` passed to `_check_command` raise
  `ShellAuthorizationError` (REQ-001, REQ-002); covered by REQ-004.
- Mutating `git` forms (`git branch -D feature`, `git push`) raise
  `ShellAuthorizationError`; read-only `git` (`git log`, `git status`) still pass
  (REQ-002); covered by REQ-004.
- An unrecognized argument shape for an allowlisted executable fails closed (raises
  before any subprocess launch) (REQ-001); covered by REQ-004.
- The `command_allowlist` comment documents permitted argument shapes per command and
  that code-executing/mutating forms are rejected (REQ-003).
- Existing `_check_command` tests (`ls`/`echo`) still pass; no subprocess is launched in
  the new tests (REQ-004).

## Tests
Unit tests in `tests/mcp_servers/shell/test_shell_command_arg_contract.py`, using the
shipped allowlist semantics via `_make_service`/`ShellPolicy`:
- `python -c "..."` and `python3 -c "..."` rejected (REQ-001, REQ-002).
- `git branch -D x`, `git push`, `git reset --hard` rejected; `git log`, `git status`
  accepted (REQ-002).
- `ruff check .`, `mypy path` accepted; an unknown flag pattern for a contract that does
  not permit it fails closed (REQ-001).
- A command whose basename is allowlisted but has an uncontracted argument shape fails
  closed (REQ-001).
- Assertions fire on the exception raised by `_check_command` before any subprocess is
  built; no real command executes (REQ-004).
Regression: run the shell server test suite plus `ruff` and
`mypy --no-namespace-packages` on touched files (REQ-004).

## Documentation Impact
The change touches `config/shell_mcp_server.toml` (comment only) and
`scripts/mcp_servers/shell/shell_service.py` (module docstring already records ADR-014).
No `docs/*.md` file requires updating for this Plan; the permitted-shape description lives
in the config comment and the code contract, not in a design doc. `N/A: no docs/*.md
update required` (REQ-003).

## Assumptions
- The operator keeps `python`/`python3`/`pytest`/`git` in `command_allowlist` as-is; this
  Plan constrains their argument shapes rather than removing the entries.
- The contract is deny-by-default within each command's entry: an argument shape absent
  from a command's permitted shapes fails closed, so the shipped contract need not
  enumerate every safe flag. Allowlisted commands without a contract entry (e.g. simple
  utilities such as `ls`/`echo`) pass through the basename gate unchanged, preserving
  backward compatibility; an operator who wants stricter control over another command adds
  a contract entry for it.
- Argument-shape policy (which specific shapes each command may use) is an operator
  decision expressed by editing the contract table; the shipped contract defaults to
  fail-closed for interpreter free-form code and mutating git.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Which exact argument shapes each allowlisted command may use (e.g. whether `python`/`pytest` should ever be permitted beyond `--help`, which `git` subcommands are safe). | Operator policy; not derivable from code. | The contract is deny-by-default, so the shipped default fails closed and the operator narrows/widens it by editing the table in `shell_service.py`. No code change is blocked on this decision. | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/mcp_servers/shell/shell_service.py` | Modify | Low — `_check_command` is called only by `run_command`; no external caller. | N/A | N/A | not applicable (rsynced) |
| `tests/mcp_servers/shell/test_shell_command_arg_contract.py` | Create | Low — new test module; existing shell tests use `ls`/`echo`/env filtering, not contracted commands. | N/A | N/A | not applicable (rsynced) |
| `config/shell_mcp_server.toml` | Modify | None — comment-only change. | N/A | N/A | not applicable (rsynced) |

## Design
The contract is a module-level, deny-by-default table in
`scripts/mcp_servers/shell/shell_service.py`, keyed by executable basename. Each entry
describes the permitted argument shapes for that basename. `_check_command` runs the
basename allowlist match first (unchanged), then, for a basename that has a contract entry, validates `argv[1:]` against that
contract. A basename with no contract entry passes through unchanged (the basename
allowlist remains its sole check), preserving the existing `ls`/`echo` behavior. An
argument shape outside a contract's permitted shapes raises `ShellAuthorizationError`
before `run_command` builds the subprocess argv.

Contract representation: a mapping `basename -> Contract`, where a `Contract` declares
either an allowlist of permitted leading tokens/subcommands and/or explicit forbidden
patterns (e.g. a `-c`/`-C` code flag for interpreters, or mutating git subcommands).
Keep the representation small and data-driven so adding a command is a table entry, not
new control flow. The shipped contract:

- `git`: permit read-only leading subcommands (`log`, `show`, `status`, `diff`,
  `blame`, `ls-files`, `for-each-ref`, `rev-parse`, `cat-file`, `branch` without a
  destructive flag, `tag`, `push --dry-run`). Reject mutating subcommands
  (`push` without `--dry-run`, `pull`, `reset`, `checkout`, `switch`, `branch -D/-F`,
  `commit`, `merge`, `rebase`, force-push).
- `ruff`, `mypy`: permit static-analysis flag shapes (`check`, `lint`, `type-check`,
  `--help`, file/path operands). These do not execute arbitrary code.
- `python`, `python3`: fail closed for free-form code. Reject a `-c`/`-m <module>` /
  stdin-code invocation by default; permit only non-executing forms such as `--version`
  and `--help` unless the operator extends the table. This is where UNK-01 is expressed:
  the shipped default rejects code execution and the operator widens it by editing the
  table.
- `pytest`: inherently imports and runs repository code; the shipped default fails
  closed. Document this in the config comment so the operator sees that `pytest` in the
  allowlist does not imply safe behavior.

Design choices considered and rejected:
- Putting the contract in `ShellPolicy` (`scripts/shared/protocols/shell.py`) would
  touch a shared runtime interface and widen blast radius; keep it service-local.
- Expressing the contract in `config/shell_mcp_server.toml` is awkward for structured
  subcommand/flag logic; a Python table is clearer. The config file documents intent
  only (REQ-003).
- Routing code execution to human approval is the agent-layer concern (`shellprefix001`);
  the server layer fails closed.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above — do not restate file-level detail
independently of that frozen table. A step is a top-level numbered item (a Phase); its
checklist items are sub-tasks, and the Execution Status table has one row per step.

1. **Phase 1: Contract model + shipped table** (`scripts/mcp_servers/shell/shell_service.py`)
   - [ ] Add the deny-by-default contract model and a shipped table for `git`, `ruff`,
     `mypy`, `python`, `python3`, `pytest` (REQ-001, REQ-002).
2. **Phase 2: Wire validation into `_check_command`** (`scripts/mcp_servers/shell/shell_service.py`)
   - [ ] After the basename allowlist match, resolve the contract for `argv[0]` basename
     and validate `argv[1:]`; raise `ShellAuthorizationError` on a mismatch or missing
     contract, before returning argv (REQ-001).
   - [ ] Preserve `shlex`/`argv` parsing and empty-command rejection; do not alter sandbox,
     resource limits, or env filtering (Constraints).
3. **Phase 3: Tests** (`tests/mcp_servers/shell/test_shell_command_arg_contract.py`)
   - [ ] Add unit tests: code-execution and mutating-git forms rejected; read-only/safe
     forms allowed; unrecognized shapes fail closed; no subprocess launched (REQ-004).
4. **Phase 4: Config documentation** (`config/shell_mcp_server.toml`)
   - [ ] Rewrite the `command_allowlist` comment to state permitted argument shapes per
     command and that code-executing/mutating forms are rejected (REQ-003).
5. **Phase 5: Verification** (all touched files)
   - [ ] Run the shell server test suite, `ruff`, and `mypy --no-namespace-packages`;
     confirm existing `TestCheckCommand` (`ls`/`echo`) still passes (REQ-004).

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/mcp_servers/shell/shell_service.py::_check_command` | Unit: assert rejection of code-execution/mutating forms and allowance of safe forms before subprocess build. | `uv run pytest tests/mcp_servers/shell/test_shell_command_arg_contract.py -v` | New tests pass; old `TestCheckCommand` passes. |
| `config/shell_mcp_server.toml` | Static: comment states permitted shapes and rejection. | manual read | Comment updated, no TOML syntax error. |
| Touched `scripts/` | Format/lint/type. | `uv run ruff format --check scripts/mcp_servers/shell/shell_service.py` + `uv run ruff check ...` + `uv run mypy --no-namespace-packages scripts/` | Clean. |
| Full shell suite | Regression. | `uv run pytest tests/mcp_servers/shell/ -v` | No new failures. |

## Risks
- **Risk**: Tightening the contract could reject previously-working read-only forms if
  the shipped table omits a legitimate subcommand/flag, breaking agent workflows that
  rely on them. → **Mitigation**: ship the most common read-only git/ruff/mypy shapes,
  keep the contract data-driven so operators add shapes without code changes, and the
  fail-closed default surfaces gaps as rejections (logged) rather than silent
  execution.
- **Risk**: The `python`/`python3`/`pytest` allowlist entries remain in
  `command_allowlist`, which may mislead reviewers into thinking code execution is
  sanctioned. → **Mitigation**: REQ-003 updates the config comment to state that these
  entries are name-only and that code-executing forms are rejected by the argument
  contract.
- **Risk**: A malformed shlex token or unexpected argv shape raises inside
  `_check_command`; if uncaught it could surface a non-domain exception. → **Mitigation**:
  the contract validator raises only `ShellAuthorizationError`; existing
  `ShellValidationError` handling for empty/malformed commands is preserved.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Contract model + shipped table (`scripts/mcp_servers/shell/shell_service.py`) | In Progress | — | — | REQ-001, REQ-002 |
| 2 | Wire validation into `_check_command` (`scripts/mcp_servers/shell/shell_service.py`) | In Progress | — | — | REQ-001 |
| 3 | Tests (`tests/mcp_servers/shell/test_shell_command_arg_contract.py`) | In Progress | — | — | REQ-004 |
| 4 | Config documentation (`config/shell_mcp_server.toml`) | In Progress | — | — | REQ-003 |
| 5 | Verification (all touched files) | Pending | — | — | REQ-004 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261118-065653_01_scripts_mcp_servers_shell_shell_service.py.md | 1, 2 | Procedure | Pending | — | — |
| implementations/20261118-065653_02_tests_mcp_servers_shell_test_shell_command_arg_contract.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261118-065653_03_config_shell_mcp_server.toml.md | 4 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261117-224613_shellarg001_shellserver-allowlist-ignores-arguments.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261117-225651
- **Related target files**: scripts/mcp_servers/shell/shell_service.py, tests/mcp_servers/shell/test_shell_command_arg_contract.py, config/shell_mcp_server.toml

### Requirement Traceability

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes / AI Implementation Instruction; `_check_command` returns `argv` unchecked (Confirmed by repository evidence) | `scripts/mcp_servers/shell/shell_service.py` | 2 | Unrecognized argument shape for an allowlisted executable fails closed before any subprocess launch | `test_shell_command_arg_contract.py` unrecognized-shape rejection; existing `ls`/`echo` tests pass | Confirmed by repository evidence |
| REQ-002 | Implementation Intent / Required Changes; interpreter free-form code and mutating `git` reach execution (Confirmed by repository evidence) | `scripts/mcp_servers/shell/shell_service.py` | 1, 2 | `python -c`/`python3 -c` raise `ShellAuthorizationError`; mutating `git` raises; read-only `git` passes | `test_shell_command_arg_contract.py` code-execution and mutating-git rejection, read-only allowance | Confirmed by repository evidence |
| REQ-003 | Documentation Impact | `config/shell_mcp_server.toml` | 4 | `command_allowlist` comment documents permitted argument shapes per command and that code-executing/mutating forms are rejected | static/manual read (no TOML syntax error) | Confirmed by repository evidence |
| REQ-004 | Testing Expectations / AI Implementation Instruction | `tests/mcp_servers/shell/test_shell_command_arg_contract.py` | 3, 5 | Existing `_check_command` tests (`ls`/`echo`) still pass; no subprocess launched in new tests | run shell suite + `ruff` + `mypy --no-namespace-packages` | Explicit in issue |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261118-065653 -->