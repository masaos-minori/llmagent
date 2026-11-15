## Goal

Define one canonical frozen frozenset `ALL_SIDE_EFFECTING_TOOLS` in
`scripts/shared/tool_constants.py` covering every tool that routes through shared
`dispatch_tool()` and has a write/delete/execute/API-write/index-refresh side
effect, and delete the contradictory routing-authority comment block (lines
122-126) so the module header (lines 4-21) is the sole authority statement.
(`REQ-001`, `REQ-006`)

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- `ALL_SIDE_EFFECTING_TOOLS` equals `WRITE_TOOLS | DELETE_TOOLS | GIT_WRITE_TOOLS |
  RAG_WRITE_TOOLS | CICD_WRITE_TOOLS | GITHUB_WRITE_TOOLS | GITHUB_DANGEROUS_TOOLS |
  SHELL_TOOLS | MDQ_WRITE_TOOLS`, which today equals `tool_policy.py`'s
  `_STATIC_SIDE_EFFECT_TOOLS` (verified: `_EXEC_TOOLS == {"shell_run"}` ⊆
  `SHELL_TOOLS`; `_GITHUB_MUTATION_TOOLS == GITHUB_WRITE_TOOLS | GITHUB_DANGEROUS_TOOLS`).
  Pointing the consumers at it is behavior-preserving, not a membership change.
- `index_paths`/`refresh_index` belong in the set: they route through
  `dispatch_tool()` (`mdq_server.py:321`) and are `retryable` in
  `config/mcp_dedup.toml`, so excluding them from the dedup union is the current
  defect.
- `deploy.sh` rsyncs `scripts/` wholesale, so this Python change needs no
  `deploy.sh` update.

## Design decisions

- **Canonical membership.** Include `MDQ_WRITE_TOOLS` (`index_paths`,
  `refresh_index`). They route through `dispatch_tool()` and are `retryable`, so
  excluding them is the defect being fixed. Grounded in repository evidence.
- **Placement and type.** Define it as a module-level `frozenset[str]` alongside
  the other category sets (after `MDQ_WRITE_TOOLS`, before `RETRYABLE_TOOLS`),
  with a docstring pointing to the module header as the sole authority. Read-only
  semantics match the rest of the module.

## Alternatives considered

- **Reconstruct the union lazily in each consumer.** Rejected: that is the
  defect — local reconstruction drifts. One canonical set, imported everywhere.
- **A different symbol name (a private-prefixed variant).** Rejected:
  `server.py`'s REQ-004 boundary resolves the set by the literal name
  `ALL_SIDE_EFFECTING_TOOLS` via `getattr(..., "ALL_SIDE_EFFECTING_TOOLS", None)`;
  the name is fixed by that boundary and by `mcproute001`.

## Implementation
### Target file
`scripts/shared/tool_constants.py`

### Procedure
1. Add `ALL_SIDE_EFFECTING_TOOLS: frozenset[str]` as the union of the eight
   write/delete/execute/API-write categories plus `MDQ_WRITE_TOOLS`, built from
   the category constants already defined above it:
   `WRITE_TOOLS | DELETE_TOOLS | GIT_WRITE_TOOLS | RAG_WRITE_TOOLS |
   CICD_WRITE_TOOLS | GITHUB_WRITE_TOOLS | GITHUB_DANGEROUS_TOOLS | SHELL_TOOLS |
   MDQ_WRITE_TOOLS`.
2. Attach a docstring stating it is the single canonical side-effect
   classification for dedup and retry-suppression, and that the module header is
   the sole authority statement.
3. Delete the contradictory routing-authority comment block at lines 122-126 so
   the module header (lines 4-21) is the only authority statement.

### Method
Place the frozenset definition after `MDQ_WRITE_TOOLS` (line 94) and before
`RETRYABLE_TOOLS`. Keep it a `frozenset[str]` for read-only consistency. Do not
touch any other set, `is_write`, retry class, or approval tier.

### Details

- Membership must equal exactly
  `{"write_file","edit_file","create_directory","move_file","delete_file",
  "delete_directory","git_add","git_commit","git_checkout","git_pull","git_push",
  "rag_delete_document","trigger_workflow","github_create_branch",
  "github_create_or_update_file","github_push_files","github_create_issue",
  "github_add_issue_comment","github_create_pull_request","github_update_pull_request",
  "github_delete_file","github_merge_pull_request","shell_run","index_paths",
  "refresh_index"}`.
- `MDQ_WRITE_TOOLS` = `{"index_paths","refresh_index"}` (line 94).
- Removed comment (lines 122-126) asserts `shared.tool_registry.ToolRegistry is
  the canonical/fallback routing source`, contradicting the module header's
  "Not a routing source … ToolRegistry … is drift-detection input only".
- `scripts/mcp_servers/server.py` resolves the set via
  `importlib.import_module("shared.tool_constants")` +
  `getattr(_tool_constants, "ALL_SIDE_EFFECTING_TOOLS", None)`; the symbol name
  must match exactly or the boundary stays inert.

## Compatibility considerations

`dispatch.py`, `http_transport.py`, `tool_policy.py`, and `server.py` consume
this symbol/module (rows 02-04 and the REQ-004 boundary). Adding the symbol is
additive; deleting the comment changes no runtime behavior.

## Security considerations

This is the fail-closed-on-writes (ADR-004) classification anchor. Wrong
membership either leaves a keyless execution path (omission) or over-rejects
(false positive). Lock membership with the parity test in row 05.

## Rollback considerations
N/A: revert the commit.

## Validation plan

| Target | Strategy | Tool / Command | Expected |
|---|---|---|---|
| `scripts/shared/tool_constants.py` | Unit: `ALL_SIDE_EFFECTING_TOOLS` equals the documented union, MDQ included | `uv run python -c "import sys; sys.path.insert(0,'scripts'); from shared.tool_constants import ALL_SIDE_EFFECTING_TOOLS; print(sorted(ALL_SIDE_EFFECTING_TOOLS))"` | set equals expected members |
| Whole change | Static: mypy, ruff, import layer | `uv run mypy --no-namespace-packages scripts/`, `uv run ruff check scripts/`, `PYTHONPATH=scripts uv run lint-imports` | all pass |

## Completion criteria

- `ALL_SIDE_EFFECTING_TOOLS` exists in `tool_constants.py` and equals the
  documented union.
- The comment block at lines 122-126 is removed; the module header is the only
  authority statement.
- Static checks pass.

## Out of Scope

- Changing `is_write`, retry class, approval tier, or `WRITE_DANGEROUS`.
- Removing direct MCP routes or enforcing idempotency-key presence at the request
  boundary (`mcproute001`).
- Editing `dispatch.py`, `http_transport.py`, `tool_policy.py` (rows 02-04).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Define `ALL_SIDE_EFFECTING_TOOLS` and delete the contradictory comment | Completed | 20261116-071355 | 20261116-071355 |  |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261116-071355 | 20261116-071355 |  |

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
- **Requirement ID**: `REQ-001` (canonical side-effect set) and `REQ-006` (remove contradictory comment)
- **Source issue**: `issues/20261111-163800_sideeffect001_side-effect-classification-central.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261115-052032_sideeffect001_side-effect-classification-central.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261115-220459
- **Related target files**: `scripts/shared/tool_constants.py`