# Document secret-redaction coverage boundary for logged tool results

## Priority
Low

## Summary
Log redaction is value-based: the global `_RedactionFilter` (`scripts/shared/logger.py`) redacts `Bearer <token>` headers and secret values registered via `register_secret()` at startup. Secrets returned inside a tool's response body that were never registered are logged in plaintext. Document this coverage boundary as a Known Limitation. Do not attempt to mask tool results, because they must reach the LLM unmasked.

## Background
`scripts/shared/logger.py` attaches `_RedactionFilter` to every entry-point logger (line 174). It redacts Bearer headers and registered secret values. Auth tokens are registered at startup: `mcp_config.py:312` (MCP auth token) and `http_transport.py:84` (HTTP auth token). Tool-result full-text logs (`scripts/agent/tool_runner.py:250`, inside `_emit_tool_result`) pass through this filter.

## Problem
Value-based redaction only covers known/registered secrets plus Bearer headers. A tool that returns an unregistered secret (e.g., an API key embedded in a response body) writes it to the log file unmasked. This is an inherent limitation of value-based redaction, not a code defect, but it is undocumented, so maintainers may assume full coverage.

## Reason for Change
The dry-run / approval review surfaced the tool-result log path. The redaction behavior is correct for registered secrets, but the boundary (what IS and IS NOT covered) is not documented anywhere.

## Implementation Intent
- Document in the approval/logging subsystem docs or Known Issues: (a) what `_RedactionFilter` covers (Bearer + registered secrets), (b) that tool results pass through it, (c) the residual gap for unregistered secrets, and (d) why tool results cannot be regex-masked (they must reach the LLM intact).

## Target Files or Areas
- `scripts/shared/logger.py` (`_RedactionFilter`, `register_secret`)
- `scripts/agent/tool_runner.py` (`_emit_tool_result`)
- Approval/logging subsystem docs / Known Issues

## Required Changes
- Add a Known Limitations entry describing the value-based redaction coverage.
- Note that registering additional high-value secrets via `register_secret()` extends coverage.

## Constraints
- Do NOT add regex masking to the tool-result path: tool results must reach the LLM unmasked by design.
- Do NOT change `_RedactionFilter` behavior (that would alter production logging).

## Acceptance Criteria
- The redaction coverage boundary is documented (what is/is not covered).
- No behavioral change to logging or tool-result handling.

## Testing Expectations
Not required (documentation-only). Run the documentation consistency checker for the target docs if one exists.

## Documentation Impact
Add a Known Limitations section documenting the value-based redaction coverage and its residual gap.

## Out of Scope
- Changing `_RedactionFilter` or `register_secret` behavior.
- Masking tool results or conversation history.

## Dependencies
N/A: none

## Unresolved Questions
N/A: none

## AI Implementation Instruction
Documentation-only. State the redaction coverage boundary precisely (Bearer + registered secrets; unregistered in-body secrets pass through). Do not modify any Python behavior.

## Traceability
- Workflow phase: python-code-review -> issue-creator
- Source issue: N/A: this document is the issue
- Source requirement: N/A: no standalone requirement document is generated
- Source plan: N/A: not filed from a Plan
- Source implementation procedure: N/A: not filed from an implementation procedure
- Generated at: 20261021-161803
- Related target files: scripts/shared/logger.py, scripts/agent/tool_runner.py
```
