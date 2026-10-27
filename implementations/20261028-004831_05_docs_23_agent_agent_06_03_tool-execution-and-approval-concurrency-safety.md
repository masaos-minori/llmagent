## Goal

State the process-wide default concurrency ceiling in the Concurrency Limits section of
`docs/23_agent/agent_06_03_tool-execution-and-approval-concurrency-safety.md`, and
correct the "If the key does not exist: No limit" bullet so it reflects the bounded
default while preserving the `0`/negative opt-out (`REQ-005`).

## Scope

Modifies only the `### Concurrency Limits` subsection of
`docs/23_agent/agent_06_03_tool-execution-and-approval-concurrency-safety.md` (the
mechanism sentence at line 47 and the per-key bullet list at lines 49-51). No other
section, file, or code change.

## Assumptions

- After the seq-01 row lands, every configured server is capped: a configured positive
  value wins, an omitted key falls back to the process-wide default ceiling, and an
  explicit `0`/negative value stays unlimited. This doc describes that end state; the
  constant behind the ceiling is defined in `scripts/shared/tool_transport_invoker.py`
  by the seq-01 row, so it exists by the time code-implementation runs the rows in
  order.
- This edit is disjoint from any code-row edits to `tool_transport_invoker.py`; it
  touches only this documentation file.

## Design decisions

- Keep the existing mechanism sentence intact except for adding the default-ceiling
  clause; correct the "No limit" bullet, which becomes false once the default is
  bounded, and add the preserved `0`/negative opt-out so the section fully describes
  the effective-limit resolution.

## Alternatives considered

- Rewriting the whole Concurrency Limits subsection: rejected — only the mechanism
  sentence's missing-clause and the "No limit" bullet are stale; a minimal edit
  preserves the rest.

## Implementation
### Target file

`docs/23_agent/agent_06_03_tool-execution-and-approval-concurrency-safety.md`

### Procedure

1. Add the default-ceiling clause to the mechanism sentence (currently line 47):

   ```markdown
   `tool_concurrency_limits: dict[str, int]` in `ToolConfig` maps server keys to
   maximum concurrent calls. It is implemented as an `asyncio.Semaphore` created
   on-demand during tool execution; a server with no entry is capped at the
   process-wide default concurrency ceiling.
   ```

2. Replace the per-key bullet list (currently lines 49-51):

   ```markdown
   - If the server key exists in the limit dictionary, calls are limited to that value
   - If the key does not exist: calls fall back to the process-wide default concurrency ceiling
   - A configured `0` or negative limit opts out and stays unlimited (no semaphore)
   - Unknown server keys log a warning but do not cause errors
   ```

### Method

A one-clause addition to the mechanism sentence plus a four-bullet rewrite inside the
`### Concurrency Limits` subsection. No code, signature, or behavior change, so no test
or static-contract edit is required beyond the standard documentation checkers.

### Details

- The old mechanism sentence described the map-and-semaphore mechanism with no default,
  understating the guardrail. The old "If the key does not exist: No limit" bullet is
  now false once the default is bounded; the rewritten bullets state the fallback and
  the preserved `0`/negative opt-out.

## Compatibility considerations

Docs-only: no code or config change; the two 23_agent concurrency docs stay mutually
consistent on the bounded-default behavior.

## Security considerations

N/A: documentation text only; no behavior or access-control change.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- Documentation consistency (23_agent domain): `rules/toolchain.md` documentation
  consistency check; both 23_agent concurrency docs describe the bounded default and
  the preserved opt-out.

## Completion criteria

- The Concurrency Limits mechanism sentence states the default ceiling for servers with
  no entry, and the per-key bullets reflect the fallback and the preserved `0`/negative
  opt-out (`REQ-005`).
- No text in the repo states that an unconfigured server is unlimited (`REQ-006`).

## Out of Scope

- Any change to `scripts/shared/tool_transport_invoker.py` or `tool_executor.py`
  (constant + `_ensure_semaphores()` and the docstring, covered by earlier rows).
- Other sections of this documentation file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: `REQ-005` (both 23_agent docs describe the bounded default and the preserved opt-out)
- **Source issue**: issues/20261027-001921_mcpinv004_unbounded-per-server-concurrency-default.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261027-104612_mcpinv004_unbounded-per-server-concurrency-default.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-004831
- **Related target files**: docs/23_agent/agent_06_03_tool-execution-and-approval-concurrency-safety.md
