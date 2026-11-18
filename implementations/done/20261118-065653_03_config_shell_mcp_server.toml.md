## Goal

Rewrite the `command_allowlist` comment in `config/shell_mcp_server.toml` to state which argument shapes are permitted per command and that code-executing/mutating forms are rejected by the argument-shape contract (REQ-003).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The `command_allowlist` entries stay as-is (out of scope to change which commands appear); only the comment is rewritten.
- The contract lives in `scripts/mcp_servers/shell/shell_service.py`; the config documents intent only.

## Design decisions
- State intent and boundaries without enumerating every flag: name each allowlisted command, summarize its permitted argument shape, and explicitly note that code-executing and mutating-git forms are rejected.

## Alternatives considered
- Listing the full contract in TOML: rejected as awkward for structured subcommand/flag logic; the Python table is the source of truth and the config documents intent only.

## Implementation
### Target file
`config/shell_mcp_server.toml`

### Procedure
1. Replace the current one-line comment (`permitted command names (matched against argv[0] basename)`) with a per-command summary of permitted argument shapes and an explicit statement that code-executing and mutating-git forms are rejected by the server's argument-shape contract.

### Method
- Keep it a comment block above the `command_allowlist` key. For each entry, note the permitted shape and the rejected form: `python`/`python3`/`pytest` are name-only and code-executing forms are rejected; `git` permits read-only subcommands and rejects mutating ones (`push`, `reset`, `branch -D`, ...); `ruff`/`mypy` permit static-analysis flag shapes.

### Details
- Do not enumerate every flag; point to the deny-by-default contract in `shell_service.py` and state that operators narrow/widen permitted shapes by editing that table.

## Compatibility considerations
- Comment-only change; no TOML syntax or behavior change.

## Security considerations
- The comment now alerts operators that a `python`/`pytest` allowlist entry does not imply safe behavior — code-executing forms are rejected by the contract. Do not word it so it implies the allowlist alone constrains behavior.

## Rollback considerations
- Revert the commit; the comment is additive documentation.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `config/shell_mcp_server.toml` | Static: comment states permitted shapes and rejection. | manual read + TOML parse | Comment updated, no TOML syntax error. |

## Completion criteria
- The `command_allowlist` comment documents permitted argument shapes per command and that code-executing/mutating forms are rejected (REQ-003).

## Out of Scope

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261118-080641 |  |
| 2 | Add or update tests per Validation plan | Completed | — | 20261118-080641 | N/A: config-comment change; validation plan uses static/manual TOML read, no tests |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261118-080641 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261118-080641 | N/A: no docs/00_index.md task-scope mapping for the changed file |

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
- **Requirement ID**: `REQ-003` (config comment documents permitted argument shapes and rejection of code-executing/mutating forms)
- **Source issue**: issues/20261117-224613_shellarg001_shellserver-allowlist-ignores-arguments.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261117-225659_shellarg001_shellserver-allowlist-ignores-arguments.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-065653
- **Related target files**: `config/shell_mcp_server.toml`