## Goal

Correct the parallel-execution sentence in `docs/23_agent/agent_08_03_configuration-tools-memory.md`
so it states that a server with no `tool_concurrency_limits` entry is capped at the
process-wide default ceiling, and that an explicit `0`/negative value still opts out
(unlimited) (`REQ-005`, `REQ-006`).

## Scope

Modifies only one sentence in `docs/23_agent/agent_08_03_configuration-tools-memory.md`
(the Parallel Execution bullet, line 43). No other section, file, or code change.

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

- Keep the existing "`tool_concurrency_limits` maps a server key to its maximum
  concurrent calls" lead sentence intact; only correct the clause that described the
  unconfigured default as unlimited, which becomes false once the default is bounded.

## Alternatives considered

- Rewriting the whole Parallel Execution paragraph: rejected — only the "unconfigured
  default" clause is stale; a one-sentence correction preserves the rest.

## Implementation
### Target file

`docs/23_agent/agent_08_03_configuration-tools-memory.md`

### Procedure

1. Replace the Parallel Execution bullet (currently line 43):

   ```markdown
   - `tool_concurrency_limits` maps a server key to its maximum concurrent calls.
     Every configured server is capped at its configured positive limit, or at the
     process-wide default concurrency ceiling when it has no entry; an explicit `0`
     (or negative) value opts out and stays unlimited (no per-server semaphore is
     created).
   ```

### Method

A single-bullet replacement inside the `#### Parallel Execution` subsection. No code,
signature, or behavior change, so no test or static-contract edit is required beyond
the standard documentation checkers.

### Details

- The old bullet said a `0`/negative value means unlimited "the same as the
  unconfigured default" — after the change the unconfigured default is bounded, so that
  sentence is false. The rewritten bullet states the bounded default and the preserved
  `0`/negative opt-out.

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

- The Parallel Execution bullet no longer says an unconfigured server is unlimited; it
  states the bounded default and the preserved `0`/negative opt-out (`REQ-005`).
- No text in the repo states that an unconfigured server is unlimited (`REQ-006`).

## Out of Scope

- Any change to `scripts/shared/tool_transport_invoker.py` or `tool_executor.py`
  (constant + `_ensure_semaphores()` and the docstring, covered by earlier rows).
- Other sections of this documentation file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261028-102436 |  |
| 2 | Add or update tests per Validation plan | Completed | — | 20261028-102436 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261028-102436 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261028-102436 |  |

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
- **Requirement ID**: `REQ-005` (both 23_agent docs describe the bounded default and the preserved opt-out), `REQ-006` (no text still says an unconfigured server is unlimited)
- **Source issue**: issues/20261027-001921_mcpinv004_unbounded-per-server-concurrency-default.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261027-104612_mcpinv004_unbounded-per-server-concurrency-default.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-004831
- **Related target files**: docs/23_agent/agent_08_03_configuration-tools-memory.md