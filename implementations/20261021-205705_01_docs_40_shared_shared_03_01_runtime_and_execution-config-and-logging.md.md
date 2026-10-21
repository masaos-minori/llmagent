## Goal

Document the value-based log-redaction coverage boundary (`_RedactionFilter`: Bearer
headers + registered secrets) and its residual gap (unregistered in-body secrets pass
through unmasked), including why tool results cannot be regex-masked, in the logging
subsystem Known Limitations (REQ-001, REQ-002).

## Scope

- Add a "Known Limitations" subsection to Section 3 (`Logger`) of
  `docs/40_shared/shared_03_01_runtime_and_execution-config-and-logging.md` documenting:
  (a) what `_RedactionFilter` covers (Bearer + registered secrets), (b) that tool-result
  full-text logs pass through it, (c) the residual gap for unregistered in-body secrets,
  and (d) why tool results cannot be regex-masked (they must reach the LLM intact).
- Note that registering additional high-value secrets via `register_secret()` extends
  coverage.

## Assumptions

- The Known Limitations belongs in the logging config doc's Logger section (the
  redaction mechanism lives in the logging subsystem and that doc already carries the
  redaction bullet).
- No doc-consistency or doc-structure check currently exists that this addition would
  trip beyond the standard docs quality/content-policy checkers.

## Design decisions
- Add a "Known Limitations" subsection within Section 3 under the existing
  "Secret redaction" bullet, matching the doc's heading convention (subsection within
  Section 3). Do not create a top-level section.

## Alternatives considered
- Placing this in the security overview doc: rejected; the redaction mechanism lives in
  the logging subsystem and the logging config doc already carries the redaction bullet.

## Implementation
### Target file
`docs/40_shared/shared_03_01_runtime_and_execution-config-and-logging.md`

### Procedure
1. Read Section 3 (`Logger`), focusing on the "Secret redaction" bullet (line 63).
2. Add a "Known Limitations" subsection immediately after the "Secret redaction" bullet
   documenting:
   - **Coverage**: `_RedactionFilter` (attached to every entry-point logger in
     `Logger._configure_logger`, line 174) redacts `Bearer <token>`-pattern matches and
     exact matches against values registered via `register_secret()`. Auth tokens are
     registered at startup: `scripts/shared/mcp_config.py:312` (MCP auth token) and
     `scripts/shared/http_transport.py:84` (HTTP auth token). (This restates line 63 for
     context; the emphasis here is the *boundary*, not a duplicate description.)
   - **Tool-result pass-through**: full-text tool-result logs emitted inside
     `_emit_tool_result` (`scripts/agent/tool_runner.py`, ~line 246) pass through
     `_RedactionFilter` unchanged — the filter only touches `record.msg` for Bearer /
     registered-secret matches; it does not scan arbitrary result bodies.
   - **Residual gap**: a tool that returns an unregistered secret (e.g. an API key
     embedded in a response body) writes it to the log file unmasked. This is an inherent
     limitation of value-based redaction, not a code defect.
   - **Why no regex masking**: tool results must reach the LLM intact, so they cannot be
     regex-masked in the log path without also corrupting what the LLM sees.
   - **Extending coverage**: registering additional high-value secrets via
     `register_secret()` extends coverage.
3. Match the existing bullet style (bold lead-in + statement) used in Section 3.

### Method
- Locate Section 3 with `grep -n "## 3. \`Logger\`\|Secret redaction" docs/40_shared/shared_03_01_runtime_and_execution-config-and-logging.md`.
- Confirm the tool-result log path by reading `scripts/agent/tool_runner.py` around
  `_emit_tool_result` (currently ~L246, called from L206); do not edit that file.
- Resolve UNK-01 with an `rg` audit of other tool-result log sites (search for
  `_emit_tool_result` callers and any raw tool-result logging) — non-blocking.
- Verify the doc is English-only before finishing (the new body must be English).

### Details
- Existing "Secret redaction" bullet (line 63) already states: `_RedactionFilter`
  redacts `Bearer <token>`-pattern matches and exact matches against registered values;
  `mcp_config._build_single_server()` calls `register_secret()` on each resolved MCP
  `auth_token` after `resolve_env_ref()`.
- `_RedactionFilter` operates on `record.msg` only (see `scripts/shared/logger.py`
  L65-69, L69+); it does not post-process tool-result bodies.
- The doc has no existing "Known Limitations" section; this is the first.

## Compatibility considerations
N/A: documentation-only change; no code, interface, config, or logging-behavior impact.

## Security considerations
State the boundary precisely: coverage is Bearer headers + registered secrets only;
unregistered in-body secrets pass through. MUST NOT imply full secret protection, which
would overstate the redaction guarantee and could give maintainers false confidence.

## Rollback considerations
Revert the commit.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/40_shared/shared_03_01_runtime_and_execution-config-and-logging.md` | Documentation structure | `uv run python tools/check_docs_quality.py` | Passes; no new findings |
| `docs/40_shared/shared_03_01_runtime_and_execution-config-and-logging.md` | Content policy (no implementation-detail leakage) | `uv run python tools/check_docs_content_policy.py` | Passes; no new findings |
| `docs/40_shared/shared_03_01_runtime_and_execution-config-and-logging.md` | English-only | `uv run python tools/check_docs_japanese.py` | Passes; no Japanese text |

## Completion criteria
- A "Known Limitations" subsection exists in Section 3 (`Logger`) stating the redaction
  coverage boundary, the tool-result pass-through, the unregistered-secret residual gap,
  and why tool results cannot be regex-masked (REQ-001, REQ-002).
- The docs quality and content-policy checkers pass with no new findings.

## Out of Scope
- Changing `_RedactionFilter` or `register_secret` behavior.
- Adding regex masking to the tool-result path.
- Masking tool results or conversation history (they must reach the LLM unmasked by design).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the Known Limitations subsection to Section 3 (Logger) (REQ-001, REQ-002) | Pending | — | — | |
| 2 | Run the documentation consistency / quality checkers | Pending | — | — | |

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
- **Requirement ID**: `REQ-001`, `REQ-002`
- **Source issue**: issues/20261021-161803_secret_redaction_coverage_boundary.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261021-202906_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261021-205705
- **Related target files**: docs/40_shared/shared_03_01_runtime_and_execution-config-and-logging.md
