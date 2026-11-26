## Goal

Redact the endpoint URL stored in the probe result so status display never carries a
credential-bearing URL (REQ-005 — normal CLI output is safe for terminal capture).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- `endpoint` is filled from `cfg.url` at `scripts/agent/services/mcp_status.py` line 199; the value is
  later rendered verbatim by `scripts/agent/commands/cmd_mcp.py` (document 08), so redaction must
  happen here, at the data boundary.
- No overlap with a sibling Plan on this file.

## Design decisions

- Redact at the producer (`McpProbeResult` construction) rather than in the display formatter, so
  every consumer of the probe result receives an already-safe value (Plan D5).
- Use `redact_url` from `scripts/agent/secrets_masker.py` (document 01); no local URL handling.

## Alternatives considered

- Redacting inside the display formatter — rejected: the probe result is also consumed by other
  report paths, and redacting only at display leaves the raw URL in the data structure.

## Implementation
### Target file
`scripts/agent/services/mcp_status.py`
### Procedure
- Wrap the `endpoint` value with `redact_url` (document 01) when building `McpProbeResult`.

### Method
- `endpoint=redact_url(cfg.url) if cfg.transport == TransportType.HTTP else ""`.

### Details
- The configured URL is not mutated; only the value placed in the result is redacted.
- Empty non-HTTP endpoints stay empty strings.

### Companion test files
- `tests/agent/services/test_agent_mcp_status.py`
  - Procedure: assert the probe result's endpoint contains no userinfo, query, or fragment.
  - Validation: `uv run pytest tests/agent/services/test_agent_mcp_status.py`.

## Compatibility considerations

- Field name and type are unchanged; only the value changes.

## Security considerations

- AC-1 boundary: the probe result is display data that reaches terminal capture.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- Unit — `uv run pytest tests/agent/services/test_agent_mcp_status.py`.
- Sequence: format → lint → type → arch → security.

## Completion criteria

- A configured URL with credentials produces a probe result whose endpoint has no userinfo, query,
  or fragment, while the non-HTTP case still yields an empty string.

## Out of Scope

- Row rendering in `scripts/agent/commands/cmd_mcp.py` (document 08).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | companion `tests/agent/services/test_agent_mcp_status.py` |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-005` (normal CLI output carries no credential-bearing URL)
- **Source issue**: `issues/20261119-145307_cliplc009_redaction-stderr-diagnostics.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261126-210258_cliplc009_redaction-stderr-diagnostics.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-225455
- **Related target files**: `scripts/agent/services/mcp_status.py`, `tests/agent/services/test_agent_mcp_status.py`
