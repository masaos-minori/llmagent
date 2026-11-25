# Enforce the RAG MCP startup posture and dependency readiness on every launch path

## Priority
High

## Summary
Run the security-posture gate from the FastAPI lifespan so an imported ASGI app cannot serve tools after a failed posture, and make `/health` probe the configuration the running process uses and the dependencies it needs.

## Background
Verified against master on 2026-11-25 (source: `memo-issue.md` H-02):
- Confirmed: the gate `_enforce_posture_gate()` runs only under `if __name__ == "__main__"` (`scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`, end of file). `_lifespan` only starts the service. `_security_posture` is built at import time, so an ASGI import has the posture but never refuses to serve; `/health` reports `ready` from `validated` through `make_health_response`, but `/v1/call_tool` stays available.
- Confirmed: `_check_health_deps()` calls `ConfigLoader().load("rag_pipeline_mcp_server.toml")` on every request instead of using the process configuration, and probes only the embedding endpoint (`rag_pipeline_health_probe.py`).
- Confirmed: `make_health_response` already carries a `liveness: True` field, so liveness and readiness are not yet separate states but liveness is already unconditional.
- Not verified: how `/opt/llm/bin/mcp_rag_pipeline` and the service definitions launch the app (the source note lists them as missing information).

## Problem
An ASGI launch (for example `uvicorn mcp_servers.rag_pipeline.rag_pipeline_server:app`) can serve tools while the posture is failed, and health can probe a different endpoint than the live pipeline after a configuration file change. Readiness does not cover the RAG DB, sqlite-vec load, or the LLM dependency.

## Reason for Change
The posture gate is a startup safety control; a launch path that bypasses it makes the control unreliable.

## Implementation Intent
Gate at the start of the lifespan using the existing posture object and refuse to publish tools or readiness until it validates; keep one behavior for direct, ASGI, test-client, and launcher starts. Probe from the process's immutable configuration (the DTO from issues/20261125-093146_ragrem001_rag-runtime-tool-contracts.md), and add bounded RAG DB, sqlite-vec load, embedding, and conditional LLM probes with a non-secret fingerprint in the details.

## Target Files or Areas
- `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`, `rag_pipeline_health_probe.py`, `rag_pipeline_security.py`
- `scripts/mcp_servers/server.py`, `scripts/mcp_servers/health_response.py`
- `tests/mcp_servers/rag_pipeline/`

## Required Changes
- Invoke the posture gate at the start of the lifespan; exit non-zero (or fail the lifespan) on a failed gate; no tool dispatch before the gate passes.
- Replace the per-request config reload with the active DTO.
- Add bounded probes: RAG DB read and required tables, sqlite-vec load (not only path existence), the embedding endpoint, and the LLM endpoint only when MQE, rerank, or Refiner need it.
- Separate liveness from readiness semantics, or document the existing split.
- Add the runtime configuration fingerprint to readiness details.
- Keep the dedup health block (`dedup_health_details`) unchanged.

## Constraints
- Keep `make_health_response` as the shared builder and the existing readiness derivation.
- Probes must be time-bounded; liveness must not depend on external services.
- Do not log database paths, the extension path, or internal hosts.

## Acceptance Criteria
- Direct module start, ASGI import start, and test-client start all reject a failed posture.
- No tool dispatch or readiness answer is available before the gate succeeds.
- Editing the TOML after startup does not change the endpoints probed by the running process.
- Readiness fails for an unreadable DB, a missing required table, a sqlite-vec load failure, an unreachable embedding service, or a required unreachable LLM service.
- Liveness stays bounded.

## Testing Expectations
Unit tests for each startup path and each probe failure; existing health-detail equality tests updated; whole-suite run and changed-path gates.

## Documentation Impact
Update the MCP startup and health document (`docs/22_mcp/mcp_02_02_startup-modes-and-health.md`) with the gate placement and readiness definition.

## Out of Scope
- Agent-side startup validation (issues/20261125-093148_ragrem003_rag-consistency-structured-probes.md).
- Comparing Agent and RAG MCP database paths.

## Dependencies
- Depends on issues/20261125-093146_ragrem001_rag-runtime-tool-contracts.md (the immutable runtime DTO).

## Unresolved Questions
- `不明`: how production launches the server (generator of `/opt/llm/bin/mcp_rag_pipeline`, init scripts); confirm before fixing the exit-code behavior.
- `不明`: whether a gate failure should end the process or only fail the lifespan under an ASGI server that owns the process.

## AI Implementation Instruction
Reuse the existing posture object and health builder; do not add a new status service; stop and ask if the launcher cannot honor a lifespan failure.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261125-093147
- **Related target files**: `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`, `scripts/mcp_servers/rag_pipeline/rag_pipeline_health_probe.py`, `scripts/mcp_servers/rag_pipeline/rag_pipeline_security.py`
