# MDQ MCP server lacks pre-bind fail-closed security posture gate

## Priority
Medium

## Summary
Every MCP server except `mdq-mcp` calls `_enforce_posture_gate()` in its `__main__` before `MCPServer.run_http()`, which exits the process before binding if the security posture is invalid. `mdq_server.py` does not call this gate; it evaluates its security posture only on the `/health` probe. Add the same pre-bind fail-closed posture gate to `mdq-mcp` (or confirm that `/health`-based detection is the intended model and document the deviation).

## Background
The MCP server base class `MCPServer.run_http()` enforces loopback binding and config isolation, but each server's own security-posture validation is expected to run as a fail-closed gate before binding. Today every MCP server implements this in its entry point: `web_search`, `file` (read/write/delete), `github`, `git`, `shell`, `cicd`, and `rag_pipeline` all define `_enforce_posture_gate()` and call it in `__main__` before `run_http()`. Each has a dedicated `test_*_health_posture.py` that invokes the gate and asserts fail-closed startup. `mdq-mcp` has no `_enforce_posture_gate()` and no corresponding test; its only startup guard is a module-level check that rejects an empty Bearer token. Its full security posture is computed by `check_health()` and published on the `/health` endpoint only.

## Problem
`mdq_server.py`'s `__main__` calls only `server.run_http()` with no posture gate:
```python
if __name__ == "__main__":
    server = MdqMCPServer()
    server.run_http()
```
So a misconfigured MDQ server (missing DB, schema error, empty `allowed_dirs`, etc.) binds and begins listening before its misconfiguration is detected. The misconfiguration is only discovered on the next `/health` probe, after the server is already accepting connections. Every other MCP server refuses to bind instead.

## Reason for Change
This is a deviation from the shared MCP startup contract that all sibling servers follow and that ADR-003 (Static Availability) / ADR-004 (fail-closed) describe. The window between bind and first `/health` detection is unnecessary when the server could fail closed before binding like its peers.

## Implementation Intent
Bring `mdq-mcp` in line with the other servers: run its security-posture validation as a fail-closed gate in `__main__` before `run_http()`, exiting(1) when the posture is invalid. The gate should reuse the existing `validate_mdq_security()` / `build_mdq_posture()` machinery already present in `mdq_security_validation.py` rather than introduce a new validation path. If the maintainers intend MDQ to rely on `/health`-based detection by design, document the deviation explicitly instead.

## Target Files or Areas
- `scripts/mcp_servers/mdq/mdq_server.py` (`__main__`, entry point)
- `scripts/mcp_servers/mdq/mdq_security_validation.py` (`validate_mdq_security`, `build_mdq_posture`)
- `tests/mcp_servers/mdq/` (add a health-posture / fail-closed startup test mirroring the sibling servers)

## Required Changes
- Add a `_enforce_posture_gate()` function to `mdq_server.py` that runs `validate_mdq_security()` and raises `SystemExit(1)` when the posture is not validated, matching the sibling servers' pattern.
- Call `_enforce_posture_gate()` in `mdq_server.py`'s `__main__` before `server.run_http()`.
- Add a `test_mdq_health_posture.py` (or equivalent) that asserts the gate fails closed, mirroring the existing sibling tests.

## Constraints
- Must not change MDQ's security model (e.g. `allowed_dirs` per-request authorization, Bearer auth) — only add the pre-bind gate.
- Must reuse existing validation machinery; do not invent a new posture definition.
- Must not alter the module-level empty-token guard that already exists.

## Acceptance Criteria
- `mdq_server.py`'s entry point validates the security posture before binding.
- A misconfigured MDQ server exits before listening, matching sibling servers.
- A new or updated test asserts the fail-closed startup behavior.

## Testing Expectations
- Unit test for the fail-closed startup gate (mirrors sibling `test_*_health_posture.py`).
- Existing `tests/mcp_servers/mdq/` tests still pass.
- `uv run ruff check scripts/mcp_servers/mdq/mdq_server.py`, `uv run mypy --no-namespace-packages scripts/`, and `uv run bandit scripts/mcp_servers/mdq/mdq_server.py` remain clean.

## Documentation Impact
If the intended design is `/health`-based detection for MDQ, record that decision (and why MDQ differs from the other servers) as an operational note / Known Issue rather than leaving the inconsistency undocumented.

## Out of Scope
- Changing how MDQ computes or publishes its security posture on `/health`.
- Modifying the other MCP servers' gates.
- Changing `MCPServer.run_http()`.

## Dependencies
N/A: none

## Unresolved Questions
- Whether the Agent-side `startup_validation.py` already rejects a misconfigured MDQ before the subprocess launches, which would reduce the practical impact of the missing local gate. Needs confirmation against current source.
- Whether MDQ's per-request `allowed_dirs` model makes a pre-bind gate redundant by design.

## AI Implementation Instruction
Confirm whether the intended MDQ model is pre-bind fail-closed or `/health`-based. If pre-bind: add `_enforce_posture_gate()` reusing `validate_mdq_security()`/`build_mdq_posture()`, call it in `__main__` before `run_http()`, and add a fail-closed startup test mirroring the sibling servers. Do not modify the security model or other servers. If `/health`-based detection is intentional, document the deviation instead of adding a gate.

## Traceability
- **Workflow phase**: python-code-review (GitHub Issue Conversion via issue-creator)
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261018-191517
- **Related target files**: scripts/mcp_servers/mdq/mdq_server.py, scripts/mcp_servers/mdq/mdq_security_validation.py

## Verification

Overall assessment: The issue is accurate and reproducible against current source. Every factual claim holds; the core defect is real and unambiguous.

Core claim status: Holds. `mdq_server.py` has no `_enforce_posture_gate()` and its `__main__` calls only `server.run_http()`, while every sibling MCP server defines `_enforce_posture_gate()` and invokes it before `run_http()`. The MDQ posture machinery (`validate_mdq_security()`, `build_mdq_posture()`) exists and is exercised by `check_health()`, but only publishes on `/health`, never as a pre-bind gate.

Findings by severity:

- Medium — Missing pre-bind fail-closed gate. `mdq_server.py` entry point binds HTTP before any misconfiguration (missing DB, schema error, empty `allowed_dirs`) is detected; detection waits for the next `/health` probe. Evidence: sibling servers (`web_search_server.py`, `file/read_server.py`, `git_server.py`, etc.) each define `_enforce_posture_gate()` reading `_security_posture.validated` and raise `SystemExit(1)`; `mdq_server.py` has no such symbol. Confidence: High (Explicit in code).
- Medium — No corresponding test. Sibling servers each ship `test_*_health_posture.py` asserting fail-closed startup; `tests/mcp_servers/mdq/` has none. Confidence: High (Explicit in code).
- Low — Import-time posture is absent for MDQ. Siblings build their posture once at module import (`_security_posture = _build_security_posture(_cfg)`); MDQ builds it only inside `check_health()` per probe, so a pre-bind gate requires lifting posture construction to import time. Confidence: High (Explicit in code).
- Informational — Practical impact is bounded. The Agent-side `startup_validation.py` also validates via the `/health` probe rather than a pre-bind gate, so MDQ is consistent with the Agent's own model; the gap is contract inconsistency with sibling servers, not a missing control. Confidence: High (Explicit in code).

Highest severity: Medium.

Verdict: Valid, actionable issue. Recommend adding the pre-bind gate reusing existing MDQ validation machinery, and adding a fail-closed startup test mirroring the sibling servers.
