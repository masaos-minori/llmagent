# Implementation Procedure — scripts/mcp_servers/cicd/cicd_service_init.py

## Goal

Use the resolved effective credential and stop constructing `httpx.AsyncClient` at service-init time; accept an injected client from the lifespan.

## Scope
**Release unit**: shared client and probe

Requirements implemented: REQ-001 (effective credential through the resolution function), REQ-008 (lifespan-owned client, test injection kept). Acceptance criteria: AC-1, AC-6.

## Assumptions
- Test injection is preserved because tests already pass their own client to the backends (Plan D4).
- The client is created by the `cicd_server.py` row's lifespan; this document only receives it.

## Design decisions
- `build_service()` takes the client as an argument instead of creating it, following the rag-pipeline lifespan precedent (`scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`, reference only).

## Alternatives considered
- Keep construction in `build_service()` with a shutdown hook: rejected per REQ-008 — the lifespan is the single owner, and import-time construction has no shutdown path.

## Implementation
### Target file
`scripts/mcp_servers/cicd/cicd_service_init.py`

### Procedure
- Replace the inline token resolution at line 26 with `resolve_effective_credential(cfg)` from `scripts/mcp_servers/cicd/cicd_credential.py`.
- Add a client parameter to `build_service()` and remove the `httpx.AsyncClient(timeout=30.0)` construction inside it.
- Keep the existing rate-limit warning when no effective credential exists.

### Method
- Lines 24-41 currently resolve the token inline, warn only, and create the client inside `build_service()` (verified in Step 3a); the backend construction (`GitHubActionsCompositeBackend`) keeps receiving the same client object, now injected.

### Details
- The only importer is `cicd_service.py`, plus `cicd_server.py` module-level construction, which the `cicd_server.py` row moves into the lifespan.

## Compatibility considerations
- `tests/mcp_servers/cicd/test_mcp_cicd_edge_cases.py` injects a client directly (reference, not modified); the new signature must accept that path unchanged.

## Security considerations
- N/A: no security behavior changes here; the credential policy lives in the credential module.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- Unit: injected client used unchanged — `uv run pytest tests/mcp_servers/cicd/test_cicd_lifecycle.py` (companion).
- Full sequence per `rules/toolchain.md`.

## Completion criteria
- No client is created at service-init time; the injected client reaches the composite and job backends unchanged (AC-6); the effective credential equals the resolution function's value (AC-1).

## Out of Scope
- The lifespan itself (`cicd_server.py` row).

### Companion test files
- `tests/mcp_servers/cicd/test_cicd_lifecycle.py` (new)
  - Procedure: add lifespan startup and shutdown tests, repeated-construction (no client leak), and test-injection cases.
  - Validation: `uv run pytest tests/mcp_servers/cicd/test_cicd_lifecycle.py`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan (companion test file) | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | documentation is covered by the Plan's docs rows |

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
- **Requirement ID**: REQ-001, REQ-008 (effective credential, lifespan-owned client)
- **Source issue**: issues/20261119-141106_mcpci001_cicd-credential-config-contract.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-152931_mcpci001_cicd-credential-config-contract.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-145310
- **Related target files**: `scripts/mcp_servers/cicd/cicd_service_init.py`, `tests/mcp_servers/cicd/test_cicd_lifecycle.py`
