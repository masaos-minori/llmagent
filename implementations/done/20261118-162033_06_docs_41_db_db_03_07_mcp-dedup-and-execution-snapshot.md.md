## Goal

Update the "Retry classification" bullet and the "Config keys" note in
`docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md` to state the owner/mirror
relationship (`RETRYABLE_TOOLS` is the owner; the toml is a load-validated mirror)
and the new load-time rejection. (`REQ-001`, `REQ-007` docs claims match code)

## Scope
**Release unit**: N/A: not part of a release unit (Phase 3 docs update)

## Assumptions

- Docs edits describe the mechanism only, never per-tool class values, so a future
  reclassification decision (plan UNK-02) cannot stale them (plan Risks).
- Lands after procedures 01-03 in `seq` order, i.e. after the gate exists in code.

## Design decisions

- Edit exactly two spots: the "Retry classification" bullet (`:62-63`) and the
  "Config keys" paragraph (`:71-75`); no other section change.

## Alternatives considered

- N/A: documentation claim fix with a single wording target.

## Implementation
### Target file
`docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md`

### Procedure
1. In the "Retry classification" bullet (`:62-63`): state that the owner of the
   classification is `RETRYABLE_TOOLS` in `scripts/shared/tool_constants.py`, that
   `[retry_class]` in `config/mcp_dedup.toml` is its mirror validated at load (unknown
   tool names, disallowed values, and contradictions with the owner are rejected), and
   that unknown tools still default to `non_retryable` at lookup.
2. In the "Config keys" paragraph (`:71-72`): change "the `[retry_class]` map" to note
   it is load-validated against `RETRYABLE_TOOLS` and known tool names.

### Method
Keep sentence density and the surrounding bullet structure unchanged (docs quality
rules: no implementation-detail dumps; name the canonical symbols, not their contents).

### Details
Do not list the 22 retryable tools or per-key values in the guide.

## Compatibility considerations

- N/A: docs-only change.

## Security considerations

- N/A: docs-only change.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md`, `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_docs_consistency.py --domain db` (routing.md Tools: docs scope) — all clean.

## Completion criteria

- The guide presents the toml as the load-validated mirror of `RETRYABLE_TOOLS`
  (AC-2 wording, AC-6 checkable claim).

## Out of Scope

- `docs/23_agent/agent_06_01_...` (covered by procedure 07).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the two claim spots | Completed | 2026-11-18 | — |  |
| 2 | Run the docs checkers (routing.md Tools, docs scope) | Completed | 2026-11-18 | 2026-11-18 |  |

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
- **Requirement ID**: `REQ-001` (owner/mirror relationship), `REQ-007` (guide claim fix)
- **Source issue**: issues/20261117-123018_adrchk018_mcp-retry-classes.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261118-153543_adrchk018_mcp-retry-classes.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-162033
- **Related target files**: `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md`