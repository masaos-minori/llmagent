## Goal

Add a deny-by-default per-command argument-shape contract to `ShellService._check_command`, evaluated after the existing basename allowlist match, so an allowlisted interpreter (`python`, `python3`) cannot run free-form code and `git` cannot run mutating subcommands through `shell_run` (REQ-001, REQ-002).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `_check_command` remains the single choke point: `run_command` calls it (line 268) before any subprocess is built, so a contract check inside it runs before execution.
- Allowlisted commands without a contract entry (`ls`, `echo`, ...) pass through the basename gate unchanged, preserving existing behavior.
- The contract is operator policy expressed by editing the table; the shipped default fails closed for interpreter code execution and mutating git.

## Design decisions
- Represent the contract as a module-level mapping keyed by executable basename, where each entry declares permitted leading tokens/subcommands and/or explicit forbidden patterns. Data-driven so adding a command is a table entry, not new control flow.
- Raise `ShellAuthorizationError` (the existing domain exception) on a rejected shape, before `run_command` builds the subprocess argv, so the fail-closed boundary is preserved.

## Alternatives considered
- Putting the contract in `ShellPolicy` (`scripts/shared/protocols/shell.py`) would touch a shared runtime interface and widen blast radius; rejected in favor of a service-local table.
- Expressing the contract in `config/shell_mcp_server.toml` is awkward for structured subcommand/flag logic; a Python table is clearer and the config documents intent only (REQ-003).

## Implementation
### Target file
`scripts/mcp_servers/shell/shell_service.py`

### Procedure
1. Add a module-level, deny-by-default contract table keyed by basename, covering `git`, `ruff`, `mypy`, `python`, `python3`, `pytest` (REQ-001, REQ-002).
2. In `_check_command`, after the basename allowlist match (line 126-129) and before `return argv` (line 130), resolve the contract for `argv[0]` basename and validate `argv[1:]`; raise `ShellAuthorizationError` on a mismatch or a missing contract (REQ-001).
3. Preserve `shlex`/`argv` parsing and empty-command rejection (lines 113-123); do not alter sandbox, resource limits, or env filtering.

### Method
- Insert the contract validation between line 129 (`raise ShellAuthorizationError(...)` of the basename gate) and line 130 (`return argv`). A basename that has no contract entry skips validation and returns argv unchanged.
- Keep the contract representation small and data-driven: each entry permits a set of leading subcommands and/or forbids explicit patterns (e.g. `-c`/`-m <module>` for interpreters, mutating git subcommands).

### Details
- `git`: permit read-only leading subcommands (`log`, `show`, `status`, `diff`, `blame`, `ls-files`, `for-each-ref`, `rev-parse`, `cat-file`, non-destructive `branch`/`tag`, `push --dry-run`); reject mutating subcommands (`push` without `--dry-run`, `pull`, `reset`, `checkout`, `switch`, `branch -D/-F`, `commit`, `merge`, `rebase`, force-push).
- `ruff`, `mypy`: permit static-analysis flag shapes (`check`, `lint`, `type-check`, `--help`, file/path operands).
- `python`, `python3`: fail closed for free-form code by default; permit only non-executing forms such as `--version`/`--help`.
- `pytest`: shipped default fails closed; document in the config comment that its allowlist entry does not imply safe behavior.

## Compatibility considerations
- Allowlisted commands without a contract entry are unaffected. The shipped contract is conservative; operators widen it by editing the table. A shape omitted from the shipped table now fails closed (logged) rather than executing.

## Security considerations
- This is the last technical safety boundary before execution (ADR-014). The contract is deny-by-default: anything outside a command's permitted shapes raises `ShellAuthorizationError` before the subprocess is built. Do not loosen the shipped defaults without an operator decision.

## Rollback considerations
- Revert the commit; the basename allowlist gate is unchanged and the contract is additive.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/mcp_servers/shell/shell_service.py::_check_command` | Unit: assert rejection of code-execution/mutating forms and allowance of safe forms before subprocess build. | `uv run pytest tests/mcp_servers/shell/test_shell_command_arg_contract.py -v` | New tests pass; old `TestCheckCommand` passes. |
| Touched `scripts/` | Format/lint/type. | `uv run ruff format --check scripts/mcp_servers/shell/shell_service.py` + `uv run ruff check ...` + `uv run mypy --no-namespace-packages scripts/` | Clean. |
| Full shell suite | Regression. | `uv run pytest tests/mcp_servers/shell/ -v` | No new failures. |

## Completion criteria
- `python -c`/`python3 -c` raise `ShellAuthorizationError`; mutating `git` (`git branch -D`, `git push`) raises; read-only `git` (`git log`, `git status`) passes (REQ-002).
- An unrecognized argument shape for an allowlisted executable fails closed before any subprocess launch (REQ-001).
- Existing `TestCheckCommand` (`ls`/`echo`) still passes; no subprocess launched in the new tests (REQ-004).

## Out of Scope
- The agent-side `tool_policy.py` auto-approval layer (`shellprefix001`), the sandbox, resource limits, and environment filtering. Changing which commands appear in `command_allowlist`. Routing code-executing forms to human-in-the-loop approval.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (fail-closed argument-shape validation in `_check_command`), `REQ-002` (shipped deny-by-default contract for git/ruff/mypy/python rejects code execution and mutating git)
- **Source issue**: issues/20261117-224613_shellarg001_shellserver-allowlist-ignores-arguments.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261117-225659_shellarg001_shellserver-allowlist-ignores-arguments.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-065653
- **Related target files**: `scripts/mcp_servers/shell/shell_service.py`
