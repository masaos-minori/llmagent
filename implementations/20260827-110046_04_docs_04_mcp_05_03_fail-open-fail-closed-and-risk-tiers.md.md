## Goal

Remove the stale `WRITE_DANGEROUS` caveat naming `git_checkout`/`git_pull`/
`git_push` in `docs/04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md` (REQ-004),
per `plans/20260826-113056_plan.md` and `MCP-004`'s own Resolution Notes instruction.

## Scope

- In scope: the `WRITE_DANGEROUS` row of the Risk Tier Classification table (~line
  80) only.
- Out of scope: any other row or section of this document; any code change.

## Assumptions

- `config/agent.toml::approval_risk_rules` already sets `git_checkout`/`git_pull`/
  `git_push = "high"` — re-verified 2026-08-27 at `config/agent.toml` lines 201-203.

## Design decisions

- Follow `MCP-004`'s own Resolution Notes instruction verbatim: remove the "this
  currently includes `git_checkout`, `git_pull`, and `git_push`" clause, since those
  three tools now carry the `"high"` override and behave like the other
  `WRITE_DANGEROUS` examples (`delete_file`, `shell_run`, `github_push_files`).

## Alternatives considered

- N/A: single-clause deletion in an existing table cell, directed by an existing,
  already-resolved Known Issue's own instructions.

## Implementation
### Target file
`docs/04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md`

### Procedure
1. Locate the `WRITE_DANGEROUS` row in the Risk Tier Classification table (verified
   at line 80 as of 2026-08-27).
2. Remove the trailing clause naming `git_checkout`/`git_pull`/`git_push` as falling
   back to `MEDIUM`/`y/N`.
3. Run `uv run python tools/check_docs_consistency.py --domain mcp`.

### Method
Direct text edit (Edit tool) on one table cell.

### Details
Current cell text (verified 2026-08-27, line 80):
```
Requires `yes` (full word) input **only for tools with an explicit `"high"`
override in `approval_risk_rules`** (e.g. `delete_file`, `shell_run`,
`github_push_files`). Tools without such an override fall back to the
`WRITE_DANGEROUS`→`RiskLevel.MEDIUM` tier mapping and get the `y/N` single-character
prompt instead — this currently includes `git_checkout`, `git_pull`, and `git_push`
(Explicit in code: `agent/tool_policy.py::_TIER_TO_RISK`,
`config/agent.toml::approval_risk_rules`). See `04_mcp_04_05_git.md` Approval level
for the Git-specific gap.
```
Remove the clause "— this currently includes `git_checkout`, `git_pull`, and
`git_push`" and the trailing "See `04_mcp_04_05_git.md` Approval level for the
Git-specific gap" sentence (that cross-reference described a gap that no longer
exists). The general "(e.g. `delete_file`, `shell_run`, `github_push_files`)" example
list and the `WRITE_DANGEROUS`→`MEDIUM` fallback mechanism description remain
accurate and must be kept.

## Compatibility considerations

- Documentation-only; no runtime behavior, config schema, or public interface is
  affected.

## Security considerations

- N/A: this correction only removes a stale example from a still-accurate mechanism
  description; it does not change what is documented as protected or unprotected.

## Rollback considerations

- Single-cell text revert via `git diff`/`git checkout -- <path>`; no other document
  or code depends on this exact wording.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md` | Doc consistency check | `uv run python tools/check_docs_consistency.py --domain mcp` | Passes; no new findings |

## Completion criteria

- The `WRITE_DANGEROUS` row no longer names `git_checkout`/`git_pull`/`git_push` as
  tools that fall back to the `y/N` prompt.

## Out of scope

- Any other row of the Risk Tier Classification table.
- Any code change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the stale clause from the `WRITE_DANGEROUS` row | Pending | — | — | |
| 2 | Run `uv run python tools/check_docs_consistency.py --domain mcp` | Pending | — | — | |

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
- **Requirement ID**: REQ-004
- **Source issue**: `issues/20260821_02_issue.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260826-113056_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260827-110046
- **Related target files**: `docs/04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md`
