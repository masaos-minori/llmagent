## Goal

Add a dedicated test module asserting the argument-shape contract: code-execution and mutating-git forms are rejected, read-only/safe forms are allowed, and unrecognized shapes fail closed, without launching any subprocess (REQ-001, REQ-002, REQ-004).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Tests exercise `_check_command` directly via a service built with the shipped allowlist semantics; no subprocess is launched (assert rejection before launch, or use `dry_run`).
- `_make_service`/`_make_policy` fixtures from `tests/mcp_servers/shell/test_shell_mcp_service.py` can build a service whose allowlist includes `python`, `python3`, `git`, `ruff`, `mypy`.

## Design decisions
- Use `ShellRunRequest` with `argv=` (prevents shell injection and exercises the parsed-argv path) so the contract sees the exact argv list.
- Assert the domain exception (`ShellAuthorizationError`) is raised before any subprocess is built.

## Alternatives considered
- Reusing the existing `TestCheckCommand` class instead of a new module: the plan specifies a dedicated module (`test_shell_command_arg_contract.py`) to keep the contract coverage isolated and self-documenting.

## Implementation
### Target file
`tests/mcp_servers/shell/test_shell_command_arg_contract.py` (new)

### Procedure
1. Create the module importing `_make_service`/`_make_policy` from `test_shell_mcp_service.py` and `ShellRunRequest`, `ShellAuthorizationError` from the shell package.
2. Add tests: `python -c "..."` / `python3 -c "..."` rejected; `git branch -D x` / `git push` / `git reset --hard` rejected; `git log` / `git status` accepted (REQ-002).
3. Add tests: `ruff check .` / `mypy path` accepted; an unknown flag pattern for a contract that does not permit it fails closed (REQ-001).
4. Add a test: a command whose basename is allowlisted but has an uncontracted argument shape fails closed (REQ-001).
5. Assert each rejection raises before any subprocess is built; no real command executes (REQ-004).

### Method
- Build the service with `allowed_commands` covering the contracted basenames; drive `_check_command(ShellRunRequest(argv=[...]))` and assert on the raised exception / returned argv.

### Details
- For accepted shapes, assert `_check_command` returns the argv list. For rejected shapes, assert `pytest.raises(ShellAuthorizationError)`. Keep assertions on the exception raised by `_check_command` before any subprocess is built.

## Compatibility considerations
- New module; does not touch existing tests. Existing shell tests use `ls`/`echo`/env filtering, not contracted commands.

## Security considerations
- The tests verify the fail-closed boundary: code-execution and mutating-git forms must raise before subprocess construction. Do not relax these assertions.

## Rollback considerations
- Delete the new module; it is self-contained and has no production dependency.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/mcp_servers/shell/test_shell_command_arg_contract.py` | Unit | `uv run pytest tests/mcp_servers/shell/test_shell_command_arg_contract.py -v` | All assertions pass; no subprocess launched. |
| Full shell suite | Regression | `uv run pytest tests/mcp_servers/shell/ -v` | No new failures. |

## Completion criteria
- `python -c`/`python3 -c` and mutating-git forms raise `ShellAuthorizationError`; read-only git and ruff/mypy shapes pass; unrecognized shapes fail closed; existing `ls`/`echo` tests pass.

## Out of Scope

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
- **Requirement ID**: `REQ-001` (fail-closed validation), `REQ-002` (shipped contract rejects code execution and mutating git), `REQ-004` (no subprocess launched in tests)
- **Source issue**: issues/20261117-224613_shellarg001_shellserver-allowlist-ignores-arguments.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261117-225659_shellarg001_shellserver-allowlist-ignores-arguments.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-065653
- **Related target files**: `tests/mcp_servers/shell/test_shell_command_arg_contract.py`
