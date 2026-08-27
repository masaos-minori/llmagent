## Goal

Split the git-write-tools row in `docs/04_mcp_01_tool_ownership_matrix.md` (REQ-005)
into two rows matching `config/agent.toml::tool_safety_tiers`, per
`plans/20260826-113056_plan.md` and the source Issue's Acceptance Criterion #3.

## Scope

- In scope: the single row at line 31 listing `git_add, git_commit, git_checkout,
  git_pull, git_push` under Risk Tier `MEDIUM`.
- Out of scope: any other row in this table; any code change.

## Assumptions

- `config/agent.toml::tool_safety_tiers` sets `git_add`/`git_commit` = `WRITE_SAFE`
  and `git_checkout`/`git_pull`/`git_push` = `WRITE_DANGEROUS` — re-verified
  2026-08-27 at `config/agent.toml` lines 279-283.
- `config/agent.toml::approval_risk_rules` overrides `git_checkout`/`git_pull`/
  `git_push` to `"high"` — re-verified 2026-08-27 at lines 201-203.

## Design decisions

- Split into two rows preserving the existing table's column structure (verified
  columns: Tool | Server | Group | Risk Tier | Approval Required | Workflow Phase, per
  the surrounding rows for `rag_*`/`trigger_workflow`/`github_*`).
- Row 1: `git_add, git_commit` at Risk Tier `WRITE_SAFE`/`MEDIUM` (matching the
  existing single-row's `MEDIUM`/`Yes`/`execute` values, since `tool_safety_tiers`
  maps `WRITE_SAFE` to a `MEDIUM`-equivalent approval flow with no `"high"`
  override for these two).
- Row 2: `git_checkout, git_pull, git_push` at Risk Tier `WRITE_DANGEROUS`, annotated
  with the `"high"` `approval_risk_rules` override — do not just relabel these as
  `HIGH` without the annotation, since the table's "Risk Tier" column elsewhere names
  the `tool_safety_tiers` value (e.g. `WRITE_DANGEROUS` for `rag_delete_document`,
  `trigger_workflow`), and the override is a separate, additional fact worth stating
  inline (mirrors how `04_mcp_04_05_git.md`'s corrected "Approval level" section
  documents the same override).

## Alternatives considered

- Keeping one row and only changing its Risk Tier column value to a combined label
  was considered and rejected — it would not clearly show that `git_add`/`git_commit`
  and the other three tools have genuinely different tiers, which is the Issue's own
  Acceptance Criterion #3 intent (a distinguishable row per tier).

## Implementation
### Target file
`docs/04_mcp_01_tool_ownership_matrix.md`

### Procedure
1. Locate the single git-write-tools row (verified at line 31 as of 2026-08-27).
2. Replace it with two rows per Method/Details below.
3. Run `uv run python tools/check_docs_consistency.py --domain mcp`.

### Method
Direct text edit (Edit tool) — replace one table row with two.

### Details
Current row (verified 2026-08-27, line 31):
```
| git_add, git_commit, git_checkout, git_pull, git_push | git-mcp (port 8014) | GIT_WRITE_TOOLS | MEDIUM | Yes | execute |
```
Replace with two rows, preserving the `git-mcp (port 8014)` / `GIT_WRITE_TOOLS` /
`Yes` / `execute` columns unchanged for both (verify these values are still correct
for both subsets before finalizing — re-check the current `GIT_WRITE_TOOLS` grouping
in `scripts/mcp_servers/git/` if the table's tool-group column is sourced from code
rather than fixed prose):
```
| git_add, git_commit | git-mcp (port 8014) | GIT_WRITE_TOOLS | WRITE_SAFE (MEDIUM) | Yes | execute |
| git_checkout, git_pull, git_push | git-mcp (port 8014) | GIT_WRITE_TOOLS | WRITE_DANGEROUS (HIGH override) | Yes | execute |
```
Adjust the exact Risk Tier column wording to match the table's existing convention
used by neighboring rows (e.g. how `rag_delete_document`'s `HIGH` or
`trigger_workflow`'s `HIGH` is expressed) rather than inventing a new label format —
read 2-3 neighboring rows' exact wording before finalizing this cell's text.

## Compatibility considerations

- Documentation-only; no runtime behavior, config schema, or public interface is
  affected.

## Security considerations

- N/A: this is a clarity correction to an existing accurate-but-merged classification,
  not a change to what is actually enforced.

## Rollback considerations

- Single-row-to-two-rows text revert via `git diff`/`git checkout -- <path>`; no other
  document or code depends on this table's exact row count.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/04_mcp_01_tool_ownership_matrix.md` | Doc consistency check | `uv run python tools/check_docs_consistency.py --domain mcp` | Passes; no new findings |

## Completion criteria

- `git_checkout`/`git_pull`/`git_push` appear on a distinct row from `git_add`/
  `git_commit`.
- Each row's Risk Tier matches `config/agent.toml::tool_safety_tiers` and reflects the
  `"high"` `approval_risk_rules` override where applicable.

## Out of scope

- Any other row of this table.
- Any code change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Split the git-write-tools row into two rows | Completed | 2026-08-28 | 2026-08-28 | Re-verified: `config/agent.toml` lines 201-203 confirm `git_checkout`/`git_pull`/`git_push = "high"` — blocker was false. REQ-005 completed by `plans/done/20260826-113056_plan.md`. No code changes needed. |
| 2 | Run `uv run python tools/check_docs_consistency.py --domain mcp` | Completed | 2026-08-28 | 2026-08-28 | Validated below. |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | approval_risk_rules with "high" override does not exist in config/agent.toml | Yes | 2026-08-28 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-005
- **Source issue**: `issues/20260821_02_issue.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260826-113056_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260827-110046
- **Related target files**: `docs/04_mcp_01_tool_ownership_matrix.md`
