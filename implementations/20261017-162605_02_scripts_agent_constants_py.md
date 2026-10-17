# Implementation Procedure — `scripts/agent/constants.py`

## Goal

Enable approval dry-run previews for GitHub mutation tools by adding the same nine
dry-run-capable GitHub tool names to `_DEFAULT_DRY_RUN_TOOLS` (lines 64–71) so gate 1
(`tool_name not in cfg.approval.approval_dry_run_tools`, line 82 in
`tool_approval.py`) passes by default (`REQ-002`).

## Scope

Modify only `scripts/agent/constants.py`. Append the nine GitHub tool names to
`_DEFAULT_DRY_RUN_TOOLS` (lines 64–71). Keep the existing six entries verbatim. Do NOT
touch `_DEFAULT_RESOURCE_KEYS` or any other constant. Gate 2 (`_KNOWN_DRY_RUN_CAPABLE_TOOLS`
in `tool_approval.py`) is a separate row.

## Assumptions

- `_DEFAULT_DRY_RUN_TOOLS` (lines 64–71) is a `list[str]` holding the six default tools:
  `write_file`, `edit_file`, `create_directory`, `delete_file`, `delete_directory`,
  `move_file`.
- It is the default for `approval_dry_run_tools` via
  `_get_or_default(cfg, "approval_dry_run_tools", _get_list, _DEFAULT_DRY_RUN_TOOLS)`
  (config_builders.py:312–314), then sanitized by `_validate_dry_run_tools`
  (config_builders.py:121: `supported = set(_DEFAULT_DRY_RUN_TOOLS)`).
- Row 1 adds the nine GitHub names to `_KNOWN_DRY_RUN_CAPABLE_TOOLS`; both gates must pass
  for the dry-run path to execute (REQ-002).

## Adversarial verification findings (plan discrepancies)

- **No discrepancy.** Verified:
  - `_DEFAULT_DRY_RUN_TOOLS` feeds the `approval_dry_run_tools` default (config_builders.py:312–314)
    and is validated by `_validate_dry_run_tools` (config_builders.py:121). Confirmed.
  - The six current entries match those in `tool_approval.py::_KNOWN_DRY_RUN_CAPABLE_TOOLS`.
  - Adding GitHub tools here affects all users' defaults; acceptable because GitHub tools
    only exist when a GitHub MCP server is configured and dry-run has no side effects (per
    plan's assumptions).

## Design decisions

- Append the nine names after the existing six in the list literal, preserving order and
  the surrounding comment. This is the minimal change to gate 1.
- Do NOT change how `approval_dry_run_tools` is read from config (out of scope).
- Named boundary: only the membership of `_DEFAULT_DRY_RUN_TOOLS` changes.

## Alternatives considered

- Approach (b) — enable only gate 2 + documented config: rejected for out-of-the-box
  behavior; users without an explicit `approval_dry_run_tools` setting would still see
  static previews. Approach (a) updates both defaults (REQ-002).

## Implementation

### Target file

`scripts/agent/constants.py`

### Procedure

1. Open `_DEFAULT_DRY_RUN_TOOLS` (lines 64–71).
2. After the existing six entries, add the nine GitHub tool names:
   ```python
   "github_create_or_update_file",
   "github_push_files",
   "github_delete_file",
   "github_create_issue",
   "github_add_issue_comment",
   "github_create_pull_request",
   "github_update_pull_request",
   "github_merge_pull_request",
   "github_create_branch",
   ```
3. Verify the original six entries are byte-for-byte unchanged.
4. Confirm `_DEFAULT_RESOURCE_KEYS` and other constants are untouched.

### Method

Edit the list literal inline; re-run the config-builder and preflight tests.

### Details

- Keep the names as plain string literals matching the tool registry naming.
- The list stays a single literal; do not split into a second default.

## Compatibility considerations

- Changing the default `approval_dry_run_tools` affects all users' defaults; acceptable
  because GitHub tools only matter when a GitHub MCP server is configured and dry-run has no
  side effects.
- REQ-003: the original six default tools still produce dry-run previews.

## Security considerations

Operational safety: enabling dry-run preview does not bypass the approval gate — it only
enriches the pre-approval preview. GitHub mutation tools still require approval before any
real write.

## Rollback considerations

Revert the commit to `scripts/agent/constants.py`.

## Validation plan

- Static: `uv run python -c "from agent.constants import _DEFAULT_DRY_RUN_TOOLS as d; print('github_create_issue' in d)"` → `True`.
- Unit: existing `TestCheckApprovalDryRun` regression (REQ-003) plus the new GitHub dry-run
  test (REQ-001, REQ-005).
- Command: `uv run pytest tests/agent/test_tool_approval_preflight.py -q`.
- Lint/type: `uv run ruff check scripts/agent/constants.py` and `uv run mypy
  scripts/agent/constants.py` clean.

## Completion criteria

`_DEFAULT_DRY_RUN_TOOLS` contains the nine dry-run-capable GitHub tools alongside the
original six; the config default flows through `approval_dry_run_tools`; existing default
tools are unchanged.

## Out of scope

`_KNOWN_DRY_RUN_CAPABLE_TOOLS` in `tool_approval.py` (separate row), how
`approval_dry_run_tools` is read from config, other constants, the test file (separate row),
and the doc update (none required).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add nine dry-run-capable GitHub tools to `_DEFAULT_DRY_RUN_TOOLS` | Pending | — | — | keep existing six verbatim |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: test file is a separate row |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: no doc update required |

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
- **Requirement ID**: `REQ-002` (both gating sets include GitHub tools)
- **Source issue**: `issues/done/20261017-123420_dryrun01_enable-approval-dry-run-previews-for-github-tools.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261017-152556_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261017-162605
- **Related target files**: `scripts/agent/constants.py`
