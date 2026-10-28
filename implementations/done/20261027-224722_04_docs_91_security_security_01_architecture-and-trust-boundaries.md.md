## Goal

Add the request-error cause variant to the documented `[Retry exhausted]` message
template in `docs/91_security/security_01_architecture-and-trust-boundaries.md`
so the operator-facing example reflects the cause part appended by the sibling
implementations/20261027-224722_01_scripts_shared_http_transport.py.md procedure
(REQ-005).

## Scope

- Edit only the `[Retry exhausted]` message template in the "Operator-facing
  examples" block (current line 266): append the optional request-error cause
  segment.
- Do not touch any other line of the file.
- The handler/message change this documents lives in
  scripts/shared/http_transport.py (sibling procedure); this document edits only
  the documentation file.

## Assumptions

- The template is a single physical line (line 266) inside a fenced code block;
  the edit replaces text within that line, so the line count is unchanged and
  line 266 stays valid.
- The appended segment is optional (only present when a request error occurred),
  so it is bracketed to signal optionality without altering the existing status
  presentation.
- Overlap with sibling plan
  plans/20261027-115908_mcpcompat001_remove-mcp-compat-paths.md on
  scripts/shared/http_transport.py and tests/shared/test_tool_transport_invoker.py
  is Compatible and sequenced (mcpcompat001 rebases); this Plan's edit here is
  confined to the template line and does not touch that code.

## Design decisions

- Append the cause as an optional bracketed segment between the status field and
  the `after <N> attempts` suffix, matching the fixed part order
  `tool=`, `status=`, `last_error=`, `after <N> attempts` used by the
  exhaustion-message builder in the sibling procedure.

## Alternatives considered

- N/A: documentation-only wording update.

## Implementation

### Target file

`docs/91_security/security_01_architecture-and-trust-boundaries.md`

### Procedure

Replace the `[Retry exhausted]` template in the "Operator-facing examples" block
(line 266) with a version that also shows the optional request-error cause
segment.

### Method

Current text (line 266):

```
[Retry exhausted] tool=<tool_name> status=<last retryable HTTP status> after <attempts> attempts
```

Updated text:

```
[Retry exhausted] tool=<tool_name> status=<last retryable HTTP status> [last_error=<request-error class>: <message>] after <attempts> attempts
```

### Details

- The new `[last_error=...]` segment mirrors the optional part appended by the
  exhaustion-message builder in the sibling procedure: present only when a
  request error occurred, never for a status-only sequence.
- The `<request-error class>: <message>` placeholder stands for the exception
  class name and its string message (connection/protocol text), never a raw
  response body — consistent with the doc rule that raw response bodies are not
  included.

## Compatibility considerations

- N/A: documentation-only wording update.

## Security considerations

- N/A: no data-handling change; the template already excludes raw response
  bodies, and the cause placeholder carries only connection/protocol text.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/91_security/security_01_architecture-and-trust-boundaries.md` | Documentation consistency (91_security) | `rules/toolchain.md` documentation consistency check | Template includes the request-error cause variant |

## Completion criteria

- The "Operator-facing examples" template shows the optional request-error cause
  segment alongside the tool name, status, and attempt count (AC-5).

## Out of Scope

- Editing any other line of the file.
- The handler/message implementation (sibling http_transport.py procedure).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the request-error cause variant to the [Retry exhausted] message template in docs/91_security/security_01_architecture-and-trust-boundaries.md | Completed | 20261028-103512 | 20261028-103512 | Added optional [last_error=...] segment between status and suffix |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261028-103512 | 20261028-103512 | quality/structure/content_policy(--strict)/japanese all clean; no security-domain consistency checker exists |

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
- **Related target files**: docs/91_security/security_01_architecture-and-trust-boundaries.md
