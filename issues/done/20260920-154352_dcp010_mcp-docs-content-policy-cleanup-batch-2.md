# MCP docs content policy cleanup (batch 2)

## Priority
Medium

## Summary
Remove the mechanically-derivable content flagged by `tools/check_docs_content_policy.py`
(`GV-021`) in five MCP design documents — an error-handling table, a full JSON payload
example, a default-value restatement, a plain field/type/default table, and another
error-handling table — per `skills/DESIGN.md` Docs content policy — remove/retain.

## Background
`docscope1`/`docscope2` (see `issues/done/`) established the Docs content policy and the
`check_docs_content_policy.py` detection tool. Prior MCP cleanup issues
(`issues/done/20260905-153715_dcp003_mcp_docs_content_policy_cleanup.md` and
`issues/done/20260909-200213_dcp007.../dcp008...`) already addressed earlier findings in
this domain, but a fresh tool run today still reports new findings — see Problem.

## Problem
`uv run python tools/check_docs_content_policy.py` (run 2026-09-20) reports the
following unresolved findings in MCP documents:
- `04_mcp_02_03_audit-logging-and-errors.md:67` — error-handling table (Error
  Classification Table: HTTP status / HealthRegistry action / retryability per error type)
- `04_mcp_03_06_tool-runtime-availability-metadata.md:52` — full JSON payload example
  (`/v1/tools` response sample)
- `04_mcp_04_05_git.md:88` — default-value restatement outside a table (`git_log`
  `max_entries`/`max_log_entries` defaults repeated in prose, already covered by the
  Configuration Fields table above it)
- `04_mcp_06_03_mcpserverconfig-fields-agenttoml-mcp_servers.md:22` — plain
  field/type/default table header (`agent.toml` `[mcp_servers.*]` fields)
- `04_mcp_06_08_end-to-end-tool-call-tracing.md:37` — error-handling table (`error_type`
  meaning/example-cause per value)

## Reason for Change
Each finding duplicates a claim whose canonical source is the code (`error_type` values,
`McpServerConfig` fields) or an already-present table in the same document (the
`04_mcp_04_05_git.md` case is a same-document duplicate of its own Configuration Fields
table). Per `docs/00_governance_01_documentation-policy.md` Claim Type Taxonomy, these
are `runtime-behavior`/`configuration-schema` claims whose canonical source is
`scripts/`/`shared/mcp_config.py`, not the design document.

## Implementation Intent
For each flagged table/example, apply `skills/DESIGN.md` Avoid implementation-reference
duplication and Docs content policy — remove: replace the literal listing with a
concise reference to the owning source (module, error-handling function, or config
dataclass), and keep only the design intent that is not code-derivable — e.g. why a
given error is or is not retryable, why `HealthRegistry` is or is not updated for a
given case (already present as prose above the flagged table in `04_mcp_02_03`, which
should be retained). For `04_mcp_04_05_git.md:88`, simply remove the duplicate prose
sentence since the Configuration Fields table above it already states the same default.

## Target Files or Areas
- `docs/04_mcp_02_03_audit-logging-and-errors.md`
- `docs/04_mcp_03_06_tool-runtime-availability-metadata.md`
- `docs/04_mcp_04_05_git.md`
- `docs/04_mcp_06_03_mcpserverconfig-fields-agenttoml-mcp_servers.md`
- `docs/04_mcp_06_08_end-to-end-tool-call-tracing.md`

## Required Changes
1. `04_mcp_02_03`: replace the Error Classification Table with a pointer to the
   transport-error-handling module; retain the prose above the table (Transport
   Success/Cache Hit/Rejected-by-preflight/Retry Behavior bullets) as-is — it is design
   intent, not a code-derivable listing.
2. `04_mcp_03_06`: remove the full JSON response example; keep the prose rule ("Always
   returns every implemented tool; disabled tools are never omitted") and point to the
   `/v1/tools` handler for the exact payload shape.
3. `04_mcp_04_05_git.md`: remove the duplicate default-value sentence at line 88; the
   Configuration Fields table above already states `max_log_entries` default `50`.
4. `04_mcp_06_03`: replace the `agent.toml` `[mcp_servers.*]` field/type/default table
   with a pointer to the config dataclass (`shared/mcp_config.py`); retain the "Ownership"
   note above it (design intent about which file owns which fields).
5. `04_mcp_06_08`: replace the `error_type` table with a pointer to the audit-event
   schema/emitter; retain the "Regarding cross-layer correlation" prose above it.
6. Re-run `uv run python tools/check_docs_content_policy.py` and confirm zero findings
   for these five files.

## Constraints
- Do not alter any other content in these five files beyond the flagged
  tables/examples/sentence and their immediately surrounding prose.
- Do not remove the retryability/design-intent prose that already precedes several of
  the flagged tables (see Implementation Intent) — only the mechanically-derivable part
  is in scope.

## Acceptance Criteria
- `uv run python tools/check_docs_content_policy.py` reports zero findings for the five
  files in Target Files or Areas.
- Each edited section still reads coherently and points to the owning source instead of
  restating its content.
- `uv run python tools/check_docs_structure.py` passes for the five files.

## Testing Expectations
Documentation-only change. Run `uv run python tools/check_docs_content_policy.py`,
`uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`
(scoped to the five files), and
`uv run python tools/check_docs_consistency.py --domain mcp`. No `pytest`/`mypy`/`ruff`
run required.

## Documentation Impact
Yes — this issue is itself a documentation cleanup. No `docs/*.md` outside the five
listed files should need changes.

## Out of Scope
- Any MCP document not listed in Target Files or Areas.
- Extending `check_docs_content_policy.py`'s detection rules.
- `04_mcp_04_05_git.md`'s other Implementation Notes bullets (lines 90-94) — these are
  design-intent/behavioral-gap observations, not flagged findings; leave them untouched.

## Dependencies
N/A: none — independent of the RAG/Agent/EventBus/Shared batches filed alongside this
issue (different files, no shared edit surface).

## Unresolved Questions
N/A: none — each finding above was confirmed by a direct tool run and file read on
2026-09-20.

## AI Implementation Instruction
Process the five files independently, one at a time. For each: read the flagged
line(s) and enough surrounding context to preserve meaning, replace the
mechanically-derivable listing with a canonical-source pointer, keep any prose already
identified as design intent in Implementation Intent, then re-run
`tools/check_docs_content_policy.py` scoped mentally to that file before moving to the
next. Do not touch files outside Target Files or Areas.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260920-154352
- **Related target files**: see Target Files or Areas above
