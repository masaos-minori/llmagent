## Goal

Fix two comment defects in `scripts/shared/tool_constants.py`: the GitHub-tools port
comment naming the wrong server (8012 instead of 8006), and the `RETRYABLE_TOOLS`
comment citing ADR-008 instead of ADR-004 for the retry dispatch policy.
(`REQ-004`, `REQ-005`) Comment-only; zero behavior change.

## Scope
**Release unit**: retry-class-load-gate

## Assumptions

- `mcp_endpoints.yaml` is the canonical port table (github 8006, cicd 8012, git 8014);
  the comment fix aligns the module with it (`REQ-004`).
- ADR-004 owns the retryable/non-retryable dispatch failure policy (MCP-001, MCP-002);
  ADR-008 legitimately owns only the `mcp_dedup.sqlite` disposable-store semantics, so
  the corrected comment may keep an ADR-008 reference for that part (`REQ-005`).

## Design decisions

- Edit only the two flagged comment blocks (`:133` and the `RETRYABLE_TOOLS` header
  comment at `:174-181`); remove no other comment (plan constraint).
- No code change: the module's fan-out (30+ importers) is untouched because only
  comment text changes.

## Alternatives considered

- N/A: comment-only fix; no design alternatives apply.

## Implementation
### Target file
`scripts/shared/tool_constants.py`

### Procedure
1. Change `# GitHub tools (github-mcp, port 8012)` (`:133`) to `port 8006`.
2. In the `RETRYABLE_TOOLS` comment (`:174`), replace the "(ADR-008)" owner citation
   with ADR-004 (dispatch retry policy), keeping ADR-008 only as the dedup-store
   semantics reference.

### Method
Direct comment edits in place; re-check the port against
`registry/manifests/mcp_endpoints.yaml` and the ADR choice against
`docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`
(MCP-001/MCP-002) before committing.

### Details
The existing sentences about single-source-of-truth, config isolation, and the
"Keep it in sync with config/mcp_dedup.toml [retry_class]" note stay; the sibling
procedure `implementations/20261118-162033_03_scripts_shared_mcp_dedup.py.md` makes
that sync load-enforced, so no wording change is needed here.

## Compatibility considerations

- Comments only: importers and behavior unchanged.

## Security considerations

- N/A: comment-only change.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `rg -n "port 8006" scripts/shared/tool_constants.py` and a cross-check against
  `registry/manifests/mcp_endpoints.yaml` shows github 8006, cicd 8012.
- `rg -n "ADR-004" scripts/shared/tool_constants.py` shows the corrected citation; no
  stale "(ADR-008)" owner claim remains.
- `uv run ruff check scripts/shared/` and `uv run pytest tests/shared/test_tool_constants.py -q`
  (unchanged behavior).

## Completion criteria

- Port comment matches `mcp_endpoints.yaml`; retry-class comment cites ADR-004 and
  references ADR-008 only for dedup-store semantics (AC-4); all existing tests pass.

## Out of Scope

- Any `RETRYABLE_TOOLS` membership change (report-only per `REQ-006`).
- `scripts/agent/tool_runner.py`'s parallel ADR-citation comment (plan UNK-03,
  scope-amendment candidate; not a target row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply the two comment fixes | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-004` (port comment fix), `REQ-005` (ADR citation fix)
- **Source issue**: issues/20261117-123018_adrchk018_mcp-retry-classes.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261118-153543_adrchk018_mcp-retry-classes.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-162033
- **Related target files**: `scripts/shared/tool_constants.py`
