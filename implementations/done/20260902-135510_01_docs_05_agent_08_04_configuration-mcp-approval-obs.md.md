## Goal
Satisfy `REQ-001` (record each currently configured MCP server's ADR-004 required/
non-required classification and rationale) by adding a Component Criticality
Classification subsection to `docs/05_agent_08_04_configuration-mcp-approval-obs.md`.

## Scope
Add exactly one new subsection under `## Design Intent` → `### MCP Configuration`,
placed after the existing `#### Agent-side MCP Fields` subsection (line 30-35) and
before `#### Process Isolation` (line 37). No other section of this file is touched.

## Assumptions
- Owner decision (2026-09-02, recorded in the Plan's UNK-01): all 10 currently
  configured MCP servers (`shell`, `git`, `web_search`, `file_delete`, `file_write`,
  `file_read`, `github`, `cicd`, `rag_pipeline`, `mdq`) are documented as `required`
  (status quo) — none has been assessed as satisfying all of ADR-004 Decision Group 3
  item 10's criteria, and per item 12, undefined/unassessed criticality must not be
  assumed non-required.
- The new subsection documents `McpServerConfig.required: bool` (the single,
  environment-independent field — the Plan's original evidence cited the now-obsolete
  `required_in_production`/`required_in_local` pair; corrected 2026-09-02 against
  current `scripts/shared/mcp_config.py`, per Plan Background).

## Design decisions
Table format, one row per server, matching the existing per-field bullet style already
used elsewhere in this document (`#### Agent-side MCP Fields`) — no new documentation
convention introduced.

## Alternatives considered
`docs/04_mcp_03_06_tool-runtime-availability-metadata.md` was considered and rejected
as the placement (Plan `Design` section): it covers a distinct, ADR-003-governed
per-tool concept, not ADR-004's component-level classification.

## Implementation
### Target file
docs/05_agent_08_04_configuration-mcp-approval-obs.md

### Procedure
Insert a new `#### Component Criticality Classification` subsection between the
existing `#### Agent-side MCP Fields` and `#### Process Isolation` subsections.

### Method
1. Locate line 36 (the blank line after `#### Agent-side MCP Fields`'s field list,
   before `#### Process Isolation` at line 37).
2. Insert:
   ```
   #### Component Criticality Classification

   `McpServerConfig.required: bool` (default `True`) records each MCP server's
   ADR-004 Decision Group 3 required/non-required classification. A server may be
   classified non-required only if it satisfies all of Decision Group 3 item 10's
   criteria (safe-core-processing unaffected, no security-control bypass, failure
   localizable, related tools reliably disablable, Fail-Closed rejection of calls,
   disabled-state observability, other required components stay safe, any fallback
   defined by an Accepted ADR) — undefined or unassessed criticality must not be
   assumed non-required (Decision Group 3 item 12).

   | Server (`config/agent.toml` key) | Classification | Rationale |
   |---|---|---|
   | `shell` | required | Not assessed as satisfying Decision Group 3 item 10; status quo default |
   | `git` | required | Not assessed as satisfying Decision Group 3 item 10; status quo default |
   | `web_search` | required | Not assessed as satisfying Decision Group 3 item 10; status quo default |
   | `file_delete` | required | Not assessed as satisfying Decision Group 3 item 10; status quo default |
   | `file_write` | required | Not assessed as satisfying Decision Group 3 item 10; status quo default |
   | `file_read` | required | Not assessed as satisfying Decision Group 3 item 10; status quo default |
   | `github` | required | Not assessed as satisfying Decision Group 3 item 10; status quo default |
   | `cicd` | required | Not assessed as satisfying Decision Group 3 item 10; status quo default |
   | `rag_pipeline` | required | Not assessed as satisfying Decision Group 3 item 10; status quo default |
   | `mdq` | required | Not assessed as satisfying Decision Group 3 item 10; status quo default |

   No server currently overrides `required` in `config/agent.toml`; a future
   non-required reclassification requires an explicit owner decision and an update to
   this table, per ADR-004 Decision Group 3 item 13.
   ```
3. Confirm exactly one blank line separates the new subsection from
   `#### Process Isolation`.

### Details
This table's classification values (all `required`) reflect the owner's 2026-09-02
decision (Plan UNK-01), not an assumption made during this implementation — see Plan
`Assumptions` above.

## Compatibility considerations
Documentation-only change; no code, schema, or runtime behavior affected.

## Security considerations
N/A: documenting existing default classification values, no new capability granted.

## Rollback considerations
Trivially revertable via `git revert`/`git checkout` of this single file.

## Validation plan
- `.venv/bin/python tools/check_docs_quality.py docs/05_agent_08_04_configuration-mcp-approval-obs.md` → no new issues.
- `.venv/bin/python tools/check_docs_structure.py docs/05_agent_08_04_configuration-mcp-approval-obs.md` → passes (Front Matter, headings, link reachability unaffected — no new links added).
- `.venv/bin/python tools/check_docs_consistency.py --domain agent` → no new drift reported (server list matches `config/agent.toml`'s `[mcp_servers.*]` keys).

## Completion criteria
The subsection exists, lists all 10 currently configured servers with an explicit
classification and rationale, and the file passes the Validation plan checks above.

## Out of scope
`docs/adr/ADR-004-environment-failure-handling-policy.md` — covered by its own
implementation procedure document (seq 02) for this same Plan.

## Documentation
This file is itself the Specification being updated; no separate `docs/00_index.md`
task-scope mapping applies (this is an existing document, not a new one).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Insert Component Criticality Classification subsection per Method | Pending | — | — | |
| 2 | N/A: no test to add (doc-only change) | Pending | — | — | N/A |
| 3 | Run validation sequence | Pending | — | — | |
| 4 | Documentation update | Pending | — | — | N/A: this file is the documentation being updated |

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
- **Requirement ID**: REQ-001 (record per-server ADR-004 classification and rationale)
- **Source issue**: `issues/20260831-192510_adr004_06_missing_component_criticality_specification.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260901-103154_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260902-135510
- **Related target files**: `docs/05_agent_08_04_configuration-mcp-approval-obs.md`
