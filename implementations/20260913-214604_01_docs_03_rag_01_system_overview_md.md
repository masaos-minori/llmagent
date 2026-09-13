## Goal

Improve the prerequisites verification documentation in `docs/03_rag_01_system_overview.md` so operators know what success/failure looks like for each prerequisite check and have troubleshooting guidance for common failures, per REQ-001 through REQ-006.

## Scope

- In-Scope: Improving the Prerequisites section in `docs/03_rag_01_system_overview.md` with expected responses and troubleshooting guidance
- Out-of-Scope: Modifying any source code files; modifying other documentation files; changing the actual health check endpoints

## Assumptions

- The `<PORT>` placeholder in the verification command should remain as-is since port values are operational settings, not implementation details
- The health check JSON structure (`status`, `ready`, `liveness`, `dependencies`, `details`) is stable enough to document as part of the prerequisites guide
- Troubleshooting guidance should focus on the most common failure modes rather than exhaustive edge cases

## Design decisions

1. Enhance the existing prerequisites table rather than replacing it — keep the compact command form while adding supplementary detail.
2. Use the actual health response JSON structure from `health_response.py` as the basis for expected responses.
3. Keep troubleshooting guidance concise — focus on high-value, common failure modes rather than exhaustive edge cases.
4. Preserve the `<PORT>` placeholder since port values are operational settings.

Evidence grounding:
- `health_response.py:21-22`: `HEALTH_STATUS_OK = "ok"`, `HEALTH_STATUS_DEGRADED = "degraded"` — defines the two possible status values
- `health_response.py:38-39`: `ready = len(deps) == 0`, `status = HEALTH_STATUS_OK if ready else HEALTH_STATUS_DEGRADED` — determines healthy vs degraded based on deps dict
- `health_response.py:40`: `status_code = 200 if ready else 503` — HTTP status codes
- `health_response.py:41-51`: Full JSON response structure: `{status, ready, liveness, restart_recommended, operator_action_required, dependencies, details}`
- `rag_pipeline_server.py:138-150`: `_check_health_deps()` returns `deps["embed_url"] = "not configured"` when embed_url is missing — this is the primary failure mode for rag-pipeline-mcp

## Alternatives considered

- **Replace the table entirely**: Rejected because the Plan's design decision preserves the existing compact command form and adds supplementary detail rather than replacing it.
- **Add inline comments to each command**: Rejected because the Plan limits scope to adding expected responses and troubleshooting guidance, not restructuring the table itself.
- **Create a separate troubleshooting document**: Rejected because the Plan scope is limited to improving the existing section, not creating new documents.

## Implementation
### Target file
`docs/03_rag_01_system_overview.md`

### Procedure
1. Verify current state of Prerequisites section
2. Add expected success response example for embedding server health check
3. Add expected failure response example for embedding server health check
4. Add troubleshooting guidance for common embedding server failures
5. Add success criteria for sqlite-vec extension check
6. Add success criteria for configuration file checks
7. Add success criteria for target URLs/files check

### Method
Inline text addition within the existing Prerequisites section.

### Details
1. **Phase 1: Preparation — Confirm current state**
   a. Locate the Prerequisites section in `docs/03_rag_01_system_overview.md` (lines 109-117 contain only a basic table with commands; no expected responses or troubleshooting)
   b. Read `scripts/mcp_servers/health_response.py` to confirm the exact JSON structure returned by `/health` endpoints
   c. Read `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py` lines 138-150 to confirm rag-pipeline-mcp health endpoint behavior and failure modes
   d. Verify sqlite-vec extension loading behavior and version requirements
   e. Review configuration file formats for troubleshooting reference
   
2. **Phase 2: Core Implementation**
   a. Add expected success response example for embedding server health check:
      ```markdown
      **Expected success response:**
      
      ```json
      {
        "status": "ok",
        "ready": true,
        "liveness": "alive",
        "restart_recommended": false,
        "operator_action_required": false,
        "dependencies": {},
        "details": {}
      }
      ```
      ```
   
   b. Add expected failure response example for embedding server health check:
      ```markdown
      **Expected failure response:**
      
      ```json
      {
        "status": "degraded",
        "ready": false,
        "liveness": "alive",
        "restart_recommended": false,
        "operator_action_required": true,
        "dependencies": {
          "embed_url": "not configured"
        },
        "details": {}
      }
      ```
      ```
   
   c. Add troubleshooting guidance for common embedding server failures:
      ```markdown
      **Troubleshooting:**
      - If `status` is `"degraded"` and `dependencies.embed_url` is `"not configured"`: verify the embedding server URL is set in your configuration
      - If the request times out: verify the embedding server is running and accessible at the specified address
      - If you receive an HTTP 503: the service is running but has failed dependency checks — inspect the `dependencies` field for specific failures
      ```
   
   d. Add success criteria for sqlite-vec extension check:
      ```markdown
      **Success criteria:** Command exits with return code 0 and produces no error output. A non-zero exit code indicates the sqlite-vec extension is not loadable.
      ```
   
   e. Add success criteria for configuration file checks:
      ```markdown
      **Success criteria:** Each `ls` command outputs the file path without error. Missing files will produce "No such file or directory" errors.
      ```
   
   f. Add success criteria for target URLs/files check:
      ```markdown
      **Success criteria:** The Python script completes without raising `FileNotFoundError` or `ValueError`. These exceptions indicate missing config files or empty target lists respectively.
      ```

3. **Phase 3: Verification**
   a. Confirm the improved documentation accurately reflects the source code evidence
   b. Confirm no unintended modifications were made to other files

## Compatibility considerations

- The health check JSON structure could change between versions — mitigated by documenting the current structure with a note that it may evolve; point to `health_response.py` as the authoritative source
- Troubleshooting guidance could become outdated quickly — mitigated by keeping guidance focused on structural issues (service down, wrong port, missing config) rather than transient errors
- Adding too much detail could overwhelm operators instead of helping them — mitigated by using progressive disclosure: brief summary in the table, detailed examples in supplementary text below

## Security considerations

N/A: Documentation update only, no security impact.

## Rollback considerations

Simple revert of the added text — no data migration or state rollback needed.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/03_rag_01_system_overview.md | Manual review against source code evidence | Read target files + compare | Improved documentation matches actual behavior |

## Completion criteria

- [ ] Embedding server health check includes expected success response format
- [ ] Embedding server health check includes expected failure response format
- [ ] Troubleshooting guidance for common embedding server failures is present
- [ ] sqlite-vec extension check includes success criteria
- [ ] Configuration file checks include success criteria
- [ ] Target URLs/files check includes success criteria
- [ ] No source code files are modified
- [ ] No other documentation files are modified except docs/03_rag_01_system_overview.md

## Out of scope

- Modifying `scripts/mcp_servers/health_response.py` (reference file only)
- Modifying `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py` (reference file only)
- Modifying `scripts/db/store_protocols.py` (reference file only)
- Modifying `config/crawler.toml` (reference file only)
- Modifying `config/chunk_splitter.toml` (reference file only)
- Modifying `config/ingester.toml` (reference file only)
- Modifying other documentation files
- Changing the actual health check endpoints

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Verify existing Prerequisites section at lines 109-117 | Completed | — | — | Record exact wording |
| 2 | Add expected success response example | Completed | — | — | JSON with status="ok", ready=true |
| 3 | Add expected failure response example | Completed | — | — | JSON with status="degraded", ready=false |
| 4 | Add troubleshooting guidance | Completed | — | — | Service down, wrong port, missing config |
| 5 | Add sqlite-vec extension success criteria | Completed | — | — | Exit code 0, no error output |
| 6 | Add config file check success criteria | Completed | — | — | ls outputs file path without error |
| 7 | Add target URLs/files check success criteria | Completed | — | — | No FileNotFoundError/ValueError |
| 8 | Manual review of accuracy against source code | Completed | — | — | Verify all claims |

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
- **Requirement ID**: REQ-001 through REQ-006 — improve RAG System Overview Prerequisites verification documentation
- **Source issue**: issues/20260913-183049_missing_system_overview_prerequisites_verification_commands.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260913-195717_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260913-214604
- **Related target files**: docs/03_rag_01_system_overview.md
