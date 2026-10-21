## Goal

Assert the `dry_run=True` no-op contract at the approval-preview whitelist
(`_KNOWN_DRY_RUN_CAPABLE_TOOLS`, REQ-003) and narrow the whitelist only if the audit
finds a tool whose server treats `dry_run` as advisory (REQ-002).

## Scope

- Modify `scripts/agent/tool_approval.py` only: strengthen the comment at
  `_KNOWN_DRY_RUN_CAPABLE_TOOLS` (L52-71) and conditionally remove a non-no-op tool
  from the frozenset.
- Audit every whitelisted tool's server-side `dry_run` semantics (read-only
  investigation of reference files; none modified).

## Assumptions

- The audit confirms all 15 current members honor `dry_run=True` as a hard no-op;
  REQ-002 does not fire and the change is comment-only.
- `check_approval`'s call order (preview at L172 before prompt at L186) and the
  degradation-to-text-only path (`_build_preview_with_dry_run` L90-94) are preserved.

## Design decisions

- Place the no-op contract as a comment directly above the frozenset definition so
  future additions must satisfy it (REQ-003). This documents the invariant; it adds no
  runtime enforcement beyond the existing `_is_dry_run_capable` gate.
- Keep whitelist narrowing conditional (REQ-002): a removed tool falls back to the
  static `build_preview()` path, so approvals are never blocked.

## Alternatives considered

- Runtime build-time assertion that a member performs a mutation: rejected as out of
  scope for this plan; the pre-approval dry-run itself remains the gate.
- Moving the contract into `mcp_config.py`: rejected; the whitelist lives in
  `tool_approval.py` and the comment belongs at its definition site.

## Implementation
### Target file
`scripts/agent/tool_approval.py`

### Procedure
1. **Audit (REQ-001)** — Enumerate all 15 members of `_KNOWN_DRY_RUN_CAPABLE_TOOLS`
   (L53-71). The 6 local file tools (`write_file`, `edit_file`, `create_directory`,
   `delete_file`, `delete_directory`, `move_file`) each short-circuit on
   `req.dry_run` before any filesystem mutation in
   `scripts/mcp_servers/file/{write,delete}_service.py` — confirmed no-op in source.
   The 9 `github_*` members are all in `_GITHUB_MUTATION_TOOLS`, so
   `tool_policy.check_allowed_repo` denies them at preflight (L157-163) whenever
   `approval_github_allowed_repos` is empty (the shipped default in
   `config/agent.toml`); they therefore never reach the dry-run preview today. Their
   external GitHub MCP server's `dry_run` semantics are not verifiable from this repo,
   but the preflight gate makes that moot for the shipped config. Record the per-tool
   result. Resolve UNK-01.
2. **Contract comment (REQ-003)** — Strengthen the comment at L52
   (`# Only these tools can safely receive dry_run=True during approval preview.`) to
   explicitly assert the no-op contract: membership requires that the tool's server
   performs zero side effects under `dry_run=True`. The existing comment states tools
   "can safely receive dry_run=True" but does not assert the no-op contract; extend it
   rather than add a duplicate comment.
3. **Conditional narrowing (REQ-002)** — If the audit finds a member whose `dry_run` is
   advisory, remove it from the frozenset (L53-71) so its preview degrades to text-only
   via the existing guard at L90-94. If none is found, leave the frozenset unchanged.

### Method
- Locate the frozenset with `grep -n "_KNOWN_DRY_RUN_CAPABLE_TOOLS" scripts/agent/tool_approval.py`
  (currently L53); read L52-104 to see the surrounding comment and the
  `_build_preview_with_dry_run` injection point (`dry_run=True` at L103).
- Verify `check_approval` builds the preview at L172 and prompts at L186 (ordering
  unchanged).
- For the audit, read `scripts/shared/mcp_config.py` to map each `github_*` tool to its
  server and confirm `dry_run` semantics; do not edit that file.

### Details
- `_KNOWN_DRY_RUN_CAPABLE_TOOLS` (L53-71) holds 15 tools: `write_file`, `edit_file`,
  `create_directory`, `delete_file`, `delete_directory`, `move_file`,
  `github_create_or_update_file`, `github_push_files`, `github_delete_file`,
  `github_create_issue`, `github_add_issue_comment`, `github_create_pull_request`,
  `github_update_pull_request`, `github_merge_pull_request`, `github_create_branch`.
- `_build_preview_with_dry_run` (L79-104): returns static `build_preview()` when the
  tool is absent from `cfg.approval.approval_dry_run_tools` or `tools is None` (L90-94);
  skips execution when `_is_dry_run_capable` is False (L95-99); otherwise injects
  `{**args, "dry_run": True}` at L103.
- Existing tests `test_dry_run_for_create_directory` and `test_github_tool_triggers_dry_run`
  in `tests/agent/test_tool_approval_preflight.py` already assert `execute` is called
  with `dry_run is True`; the "no downstream mutation" assertion belongs in the test-row
  document.

## Compatibility considerations
No runtime interface change. The comment is inert; the conditional narrowing removes a
member only when the audit proves its `dry_run` is advisory, routing through the
existing text-only fallback.

## Security considerations
The whitelist is the security boundary for pre-approval dry-run enrichment: the preview
executes the tool before the user approves (L172 before L186). Asserting the no-op
contract at the definition (REQ-003) makes the invariant explicit so a future addition
cannot silently reintroduce an advisory `dry_run`. If REQ-002 fires, removing the
offending tool tightens the boundary further.

## Rollback considerations
Revert the commit (comment edit; or restore the frozenset if REQ-002 removed a member).

## Validation plan
| Target | Strategy | Command | Expected |
|---|---|---|---|
| `scripts/agent/tool_approval.py` | Complexity baseline | `uv run radon cc scripts/agent/tool_approval.py -s` | `check_approval` B(10), `_build_preview_with_dry_run` B(7) — unchanged |
| `scripts/agent/tool_approval.py` | Dead-code / static security | `uv run vulture scripts/agent/tool_approval.py --min-confidence 80`; `uv run bandit scripts/agent/tool_approval.py -ll` | vulture 0 findings; bandit no issues |
| `tests/agent/test_tool_approval_preflight.py` | Unit (dry-run flow) | `uv run pytest tests/agent/test_tool_approval_preflight.py` | Extended assertions pass; existing green |
| Whole module | Type check + lint | repo type-check + lint command | Pass |

## Completion criteria
- The comment above `_KNOWN_DRY_RUN_CAPABLE_TOOLS` explicitly asserts the
  `dry_run=True` no-op contract (REQ-003).
- No whitelisted tool performs a write/delete/network action during preview (REQ-002);
  any non-no-op member removed, or none exists.
- radon/vulture/bandit clean; type check + lint pass.

## Out of Scope
- Changing which tools require approval or their risk classification.
- Changing the interactive approval UX / prompt flow for approved calls.
- Masking of preview args.
- Adding new MCP servers or changing tool registration.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Audit each whitelisted tool's `dry_run` semantics (REQ-001) | Completed | 20261021-211611 | 20261021-211611 | Read-only; resolve UNK-01 15 members (procedure said 16, corrected). 6 local verified no-op in source; 9 github members gated at preflight by empty approval_github_allowed_repos. REQ-002 does not fire. |
| 2 | Strengthen the whitelist no-op comment (REQ-003) | Completed | 20261021-211603 | 20261021-211603 |  |
| 3 | Conditionally narrow the frozenset if audit finds advisory dry_run (REQ-002) | Completed | 20261021-211603 | 20261021-211603 | Comment-only if no tool removed |
| 4 | Run validation sequence (`rules/toolchain.md`) | Completed | 20261021-211603 | 20261021-211603 |  |

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
- **Requirement ID**: `REQ-002`, `REQ-003`
- **Source issue**: issues/20261021-161803_dryrun_preapproval_tool_execution.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261021-201654_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261021-204811
- **Related target files**: scripts/agent/tool_approval.py