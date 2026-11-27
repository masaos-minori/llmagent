# Implementation Procedure — scripts/mcp_servers/cicd/cicd_service_init.py

## Goal

Use the resolved effective credential and stop constructing `httpx.AsyncClient` at service-init time; accept an injected client from the lifespan.

## Scope
**Release unit**: shared client and probe

Requirements implemented: REQ-001 (effective credential through the resolution function), REQ-008 (lifespan-owned client, test injection kept). Acceptance criteria: AC-1, AC-6.

## Assumptions
- Test injection is preserved because tests already pass their own client to the backends (Plan D4).
- The client is created by the `cicd_server.py` row's lifespan; this document only receives it.
- Step 3a verification (20261127): `build_service()` has exactly one call site, `cicd_server.py:64` at module level, which the `cicd_server.py` row moves into the lifespan. Tests inject clients into the backends directly (`tests/mcp_servers/cicd/test_mcp_cicd_edge_cases.py:22`), not through `build_service()`, so the signature change reaches only the server row.
- Step 3a verification (20261127): `tests/mcp_servers/cicd/test_cicd_lifecycle.py` does not exist yet, so this row creates it. Lifespan startup and shutdown assertions cannot be written before the `cicd_server.py` row (seq 06) adds the lifespan; this row writes the injection and repeated-construction (no client leak) cases, and the lifespan cases are added by that row.

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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261127-164243 | 20261127-164243 | files: scripts/mcp_servers/cicd/cicd_service_init.py; call site in cicd_server.py passes the injected client (temporary module-level client until procedure seq 06 moves construction into the lifespan) |
| 2 | Add or update tests per Validation plan (companion test file) | Completed | 20261127-164243 | 20261127-164243 | companion tests/mcp_servers/cicd/test_cicd_lifecycle.py created, 4 tests pass (injection, no-leak, effective credential, warning); lifespan cases deferred to procedure seq 06 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261127-164243 | — | ruff/bandit/lint-imports clean; bare-except scan via grep (ast-grep CLI not installed in this environment); mypy primary run reports only the pre-existing tools/generate_mcp_inventory.py:22 error unchanged in this batch; tests/mcp_servers/cicd/ 265 passed; full suite deferred to end of batch end-of-batch full suite: 6 failures all matching tools/known_test_failures_baseline.txt; diff-cover 96% pre-commit suppression gate: the two type: ignore[misc] suppressions in the companion test were unjustified; the test now uses monkeypatch.setattr instead, per the decision not to add suppressions in test files |
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