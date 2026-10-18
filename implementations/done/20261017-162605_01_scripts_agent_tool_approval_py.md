# Implementation Procedure — `scripts/agent/tool_approval.py`

## Goal

Enable approval dry-run previews for GitHub mutation tools so approvers see real
dry-run output instead of static text. Currently a high-risk GitHub tool that requires
approval shows only a static preview because dry-run enrichment is gated behind two
checks that GitHub tools fail (`REQ-001`, `REQ-002`).

## Scope

Modify only `scripts/agent/tool_approval.py`. Add the nine dry-run-capable GitHub tool
names to `_KNOWN_DRY_RUN_CAPABLE_TOOLS` (lines 53–61). Keep the existing six entries
(`write_file`, `edit_file`, `create_directory`, `delete_file`, `delete_directory`,
`move_file`) verbatim. Do NOT touch gate 1 (`_DEFAULT_DRY_RUN_TOOLS` in
`scripts/agent/constants.py` — separate row), the dry-run execution mechanism, or any
other MCP server's tools.

## Assumptions

- `_KNOWN_DRY_RUN_CAPABLE_TOOLS` (lines 53–61) is a `frozenset[str]` and is the sole input
  to `_is_dry_run_capable(tool_name)` (lines 65–67), which gates dry-run at line 86–90 in
  `_build_preview_with_dry_run`.
- `_build_preview_with_dry_run` enforces TWO gates before executing dry-run:
  1. config allowlist `tool_name not in ctx.cfg.approval.approval_dry_run_tools` (line 82);
  2. hardcoded capability `_is_dry_run_capable(tool_name)` (line 86). Both must pass.
- The nine GitHub mutation tools genuinely declare `dry_run: bool` in their request models
  (`github_models_file.py`: CreateOrUpdateFile/PushFiles/DeleteRepoFile;
  `github_models_issues.py`: CreateIssue/AddIssueComment;
  `github_models_pull_requests.py`: CreatePullRequest/UpdatePullRequest/MergePullRequest;
  `github_models_repository.py`: CreateBranch).
- Read-only GitHub tools (GetFileContents, GetIssue, GetPullRequest, List*, Search*) lack
  `dry_run` and are auto-approved — they never reach this gate.

## Adversarial verification findings (plan discrepancies)

- **No discrepancy.** Verified against current source:
  - `_KNOWN_DRY_RUN_CAPABLE_TOOLS` currently contains only the six non-GitHub tools; every
    `github_*` tool fails gate 2 and falls back to static preview. Confirmed.
  - All nine named GitHub tools declare `dry_run: bool` in their request models; no extra
    candidates and no missing ones (UNK-01 resolved: the nine named tools are exactly the
    dry_run-capable GitHub set).
  - Pydantic GitHub models do not forbid extra fields, so passing `dry_run=True` to a
    dry_run-capable tool is accepted; strict scoping to the nine is required (UNK-01).
  - Gate 1 (`_DEFAULT_DRY_RUN_TOOLS`) is a separate file (`constants.py`) and is handled by
    a separate row — both lists must be updated for the path to work end-to-end (REQ-002).

## Design decisions

- Add the nine names to the frozenset literal after the existing six, preserving order and
  the verbatim comment above the set. This is the minimal change to gate 2.
- Do NOT derive capability dynamically from the tool reregistry (out of scope): the plan
  keeps the explicit allowlist approach for predictability and blast-radius control.
- Named boundary: only the membership of `_KNOWN_DRY_RUN_CAPABLE_TOOLS` changes;
  `_is_dry_run_capable`, `_build_preview_with_dry_run`, and the dry-run execution path are
  untouched.

## Alternatives considered

- Deriving dry-run capability dynamically from the tool registry: rejected — out of scope
  and would change how capability is determined globally.
- Enabling only gate 2 (approach b) without changing `_DEFAULT_DRY_RUN_TOOLS`: insufficient
  for out-of-the-box behavior because gate 1 (the config allowlist default) would still
  block GitHub tools unless a user sets `approval_dry_run_tools`. Approach (a) updates both
  defaults (REQ-002).

## Implementation

### Target file

`scripts/agent/tool_approval.py`

### Procedure

1. Open `_KNOWN_DRY_RUN_CAPABLE_TOOLS` (lines 53–61).
2. After the existing six entries, add the nine GitHub tool names inside the same
   `frozenset([...])` literal:
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
4. Confirm no read-only GitHub tool name was added (REQ-004).
5. Confirm `_is_dry_run_capable` and `_build_preview_with_dry_run` are untouched.

### Method

Edit the frozenset literal inline; re-run the preflight dry-run tests.

### Details

- Keep the names as plain string literals matching the tool registry naming.
- The frozenset stays a single literal; do not split into a second set (gate 2 reads only
  this one).

## Compatibility considerations

- REQ-003: the original six default tools keep masking/preview behavior unchanged.
- REQ-004: read-only GitHub tools are not added.
- Only membership of one frozenset changes; no signature or interface change.

## Security considerations

Operational safety: GitHub mutation tools already route through approval
(`tool_policy.py::_GITHUB_MUTATION_TOOLS`, `_escalate_for_github_branch`), so enabling
dry-run preview does not bypass the approval gate — it only enriches the pre-approval
preview.

## Rollback considerations

Revert the commit to `scripts/agent/tool_approval.py`.

## Validation plan

- Unit (`tests/agent/test_tool_approval_preflight.py`, `TestCheckApprovalDryRun`):
  - `check_approval(ctx, "github_create_issue", {...})` awaits `tools.execute` with
    `{**args, "dry_run": True}` and appends dry-run text to the preview (REQ-001, REQ-005).
  - A read-only GitHub tool (e.g. `github_get_issue`) does not trigger dry-run (REQ-004).
  - Existing `test_dry_run_result_appended_to_preview` / `test_dry_run_for_create_directory`
    still pass (REQ-003).
- Command: `uv run pytest tests/agent/test_tool_approval_preflight.py -q`.
- Static: `uv run python -c "from agent.tool_approval import _KNOWN_DRY_RUN_CAPABLE_TOOLS as d; print('github_create_issue' in d)"` → `True`.
- Lint/type: `uv run ruff check scripts/agent/tool_approval.py` and `uv run mypy
  scripts/agent/tool_approval.py` clean.

## Completion criteria

A dry-run-capable GitHub tool in `approval_dry_run_tools` yields a preview containing the
dry-run output; the original six tools are unchanged; read-only GitHub tools do not trigger
dry-run.

## Out of scope

`_DEFAULT_DRY_RUN_TOOLS` in `constants.py` (separate row), the dry-run execution mechanism,
how `approval_dry_run_tools` is read from config, other MCP servers' tools, dynamic
capability derivation, the test file (separate row), and the doc update (none required).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add nine dry-run-capable GitHub tools to `_KNOWN_DRY_RUN_CAPABLE_TOOLS` | Completed | 20261018-112623 | 20261018-112623 | keep existing six verbatim |
| 2 | Add or update tests per Validation plan | Completed | 20261018-112623 | 20261018-112623 | N/A: test file is a separate row |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261018-112623 | 20261018-112623 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261018-112623 | 20261018-112623 | N/A: no doc update required |

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
- **Requirement ID**: `REQ-001` (dry-run preview for GitHub tools), `REQ-002` (both gating
  sets include GitHub tools)
- **Source issue**: `issues/done/20261017-123420_dryrun01_enable-approval-dry-run-previews-for-github-tools.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261017-152556_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261017-162605
- **Related target files**: `scripts/agent/tool_approval.py`