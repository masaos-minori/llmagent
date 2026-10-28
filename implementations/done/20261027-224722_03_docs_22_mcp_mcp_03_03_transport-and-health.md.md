## Goal

Update the retry-message description in the "**Retries**" bullet of
`docs/22_mcp/mcp_03_03_transport-and-health.md` so it states that the
`TransportError` exhaustion message may also carry the last request-error cause,
matching the behavior implemented by the sibling
implementations/20261027-224722_01_scripts_shared_http_transport.py.md procedure
(REQ-005).

## Scope

- Edit only the message-contents clause in the "**Retries**" bullet (current line
  28): add "the last request-error cause (if any)" to its enumeration.
- Do not touch any other line of the file.
- The handler/message change this documents lives in
  scripts/shared/http_transport.py (sibling procedure); this document edits only
  the documentation file.

## Assumptions

- The "**Retries**" bullet is a single physical line (line 28); the edit replaces
  text within that line, so the line count is unchanged and line 28 stays valid.
- Overlap with sibling plan
  plans/20261027-115908_mcpcompat001_remove-mcp-compat-paths.md on this file is
  Compatible and sequenced: this Plan edits the "**Retries**" bullet (line 28);
  mcpcompat001 corrects the re-export statement at line 35. Disjoint regions; the
  later implementer rebases. See the sibling http_transport.py procedure's
  Assumptions.

## Design decisions

- Add the cause as a parenthetical "(if any)" clause, parallel to the existing
  "the last retryable HTTP status (if any)", so the sentence stays accurate for
  both the request-error and status-only exhaustion paths.

## Alternatives considered

- N/A: documentation-only wording update.

## Implementation

### Target file

`docs/22_mcp/mcp_03_03_transport-and-health.md`

### Procedure

Replace the message-contents clause in the "**Retries**" bullet (line 28) so it
lists the request-error cause alongside the status field.

### Method

Current text (line 28):

```
The `TransportError` message (`"[Retry exhausted] ..."`) includes the tool name,
the last retryable HTTP status (if any), and the attempt count; raw response
bodies are not included.
```

Updated text:

```
The `TransportError` message (`"[Retry exhausted] ..."`) includes the tool name,
the last retryable HTTP status (if any), the last request-error cause (if any),
and the attempt count; raw response bodies are not included.
```

### Details

- The added clause mirrors the optional last-error detail appended by the
  exhaustion-message builder in the sibling procedure: present only when a
  request error occurred, never for a status-only sequence.
- The clause stays parenthetical "(if any)" so the sentence remains correct for
  both exhaustion paths.

## Compatibility considerations

- N/A: documentation-only wording update.

## Security considerations

- N/A: no data-handling change; the message already excludes raw response bodies.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/22_mcp/mcp_03_03_transport-and-health.md` | Documentation consistency (22_mcp) | `rules/toolchain.md` documentation consistency check | Message description matches implemented shape |

## Completion criteria

- The "**Retries**" bullet states the message includes the tool name, the last
  retryable HTTP status (if any), the last request-error cause (if any), and the
  attempt count (AC-5).

## Out of Scope

- Editing any other line of the file.
- The handler/message implementation (sibling http_transport.py procedure).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the retry-message bullet in docs/22_mcp/mcp_03_03_transport-and-health.md | Completed | 20261028-103345 | 20261028-103345 | Added "(if any)" request-error cause clause parallel to the status field |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261028-103345 | 20261028-103345 | quality/structure/content_policy(--strict)/consistency(mcp)/japanese all clean |

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
- **Requirement ID**: `REQ-005`
- **Source issue**: issues/20261027-001424_mcpinv003_discarded-transporterror-httptransport-call.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261027-103707_mcpinv003_discarded-transporterror-httptransport-call.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261027-224722
- **Related target files**: docs/22_mcp/mcp_03_03_transport-and-health.md
