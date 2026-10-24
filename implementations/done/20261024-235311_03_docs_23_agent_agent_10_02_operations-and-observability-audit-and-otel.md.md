## Goal
- State in the agent audit chapter that `args_preview` is bounded, the envelope shape, and that truncation follows masking (`REQ-006`: document the cap).

## Scope
- Add one short paragraph to `### Audit Logs` (line 30 onward) of `docs/23_agent/agent_10_02_operations-and-observability-audit-and-otel.md`; no other section changes.

## Assumptions
- The chapter documents the JSON-lines format (line 48) and `tool_approval` / `tool_exec` writers (line 50), and does not mention `args_preview` (grep 2026-10-24).
- The cap value is stated as behavior; if `tools/check_docs_content_policy.py` flags the literal value as implementation detail, name it by its meaning ("the audit args-preview limit") and point to the owning module `agent/tool_audit.py` (already listed under Owners) instead.
- The wording describes agent-side events only; MCP-side audit records are not bounded by this change.
- The code row (`scripts/agent/tool_audit.py`) is applied first so the statement matches shipped behavior.

## Design decisions
- Three facts only: preview over the limit is replaced by an object with a `preview` string and a boolean `truncated` key; the limit applies after masking; sub-limit rows are unchanged.

## Alternatives considered
N/A: documentation-only row.

## Implementation
### Target file
`docs/23_agent/agent_10_02_operations-and-observability-audit-and-otel.md`

### Procedure
1. Add the paragraph after the existing `### Audit Logs` text, in English.

### Method
- Edit in place; do not add a Related section or a heading.

### Details
- State that readers MUST treat a row carrying `truncated: true` as structurally reduced, and that this marker is distinct from the masked string value.

## Compatibility considerations
N/A: documentation-only.

## Security considerations
N/A: documentation-only; the text states masking precedes bounding.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`
- `uv run python tools/check_docs_structure.py "docs/**/*.md"`
- `uv run python tools/check_docs_content_policy.py`
- `uv run python tools/check_docs_japanese.py`
- `uv run python tools/check_docs_consistency.py --domain agent`

## Completion criteria
- The chapter states the bound, the envelope shape, and the mask-before-bound order; all checkers report no findings.

## Out of Scope
- `docs/22_mcp/mcp_06_05_reading-audit-logs.md` and `docs/41_db/` retention text.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the args-preview bound paragraph to `### Audit Logs` | Completed | — | 20261025-002450 |  |
| 2 | Run the docs checkers named in Validation plan | Completed | — | 20261025-002450 |  |

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
- **Requirement ID**: `REQ-006` (document the cap and envelope)
- **Source issue**: `issues/20261024-124138_tool005-args-preview-is-written-to-the-audit-log-unbounded.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261024-221315_args-preview-is-written-to-the-audit-log-unbounded.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261024-235311
- **Related target files**: `docs/23_agent/agent_10_02_operations-and-observability-audit-and-otel.md`