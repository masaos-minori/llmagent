# Fix critical docs folder inconsistencies — deleted file refs, wrong ports, missing configs, undefined symbols

## Priority
High

## Summary
The `docs/` folder contains multiple critical inconsistencies: references to deleted files, incorrect port numbers, non-existent configuration files, undefined function names, and unregistered CLI commands. These issues cause confusion for developers and break automated tooling that validates doc-source alignment.

## Background
The documentation consistency checker (`tools/check_docs_consistency.py`) identified 3 ERROR-level findings and numerous WARNING-level findings across the docs folder. The errors include references to files that were deleted during restructuring, a port number mismatch, and multiple warnings about missing files and undefined symbols.

## Problem
Documentation claims existence of resources (files, ports, config keys, functions, commands) that do not exist in the current codebase, leading to developer confusion and false positives in automated validation tools.

## Reason for Change
These inconsistencies undermine trust in the documentation set. Developers relying on doc references will encounter dead ends. Automated tools that validate doc-source alignment will produce noise, reducing signal quality for real issues.

## Implementation Intent
For each finding category:
1. Remove references to deleted files and update migration notes to reflect current state
2. Correct the git-mcp port number to match `config/agent.toml`
3. Update or remove references to non-existent config files, noting which ones replaced them
4. Replace undefined function names with correct names or remove references if the functions no longer exist
5. Update CLI command references to match `_COMMANDS` registry or remove stale entries

## Target Files or Areas
- `docs/04_mcp_00_document-guide.md` — deleted file references
- `docs/04_mcp_05_02_auth-profiles-and-sandboxing.md` — git-mcp port number
- `docs/03_rag_01_system_overview.md` — config file reference
- `docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md` — config file reference
- `docs/03_rag_04_03_dto-models_audit.md` — non-existent module reference
- `docs/02_deployment.md` — config key references
- `docs/01_overview-files-05-config.md` — config file references
- `docs/agent_03_03_turn-processing-flow-workflow-engine.md` — config file reference
- `docs/agent_09_02_data-layer-access-patterns.md` — file path reference
- `docs/agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md` — undefined functions
- `docs/agent_14_reference-api-generated.md` — non-existent module reference
- `docs/04_mcp_04_01_web-search-file-read-github.md` — deleted file reference, file path reference
- `docs/04_mcp_05_01_access-control-and-allowlists.md` — file path reference
- All docs referencing unregistered CLI commands

## Required Changes
- [ ] Remove references to `06_ref-mcp.md`, `04_spec_mcp.md`, `04_mcp-protocol.md` from `docs/04_mcp_00_document-guide.md` or update Migration Notes to reflect their deletion
- [ ] Remove reference to `04_mcp_04_06_browser.md` from `docs/04_mcp_04_01_web-search-file-read-github.md` or update browser-mcp merge note
- [ ] Change git-mcp port from 8000 to 8014 in `docs/04_mcp_05_02_auth-profiles-and-sandboxing.md`
- [ ] Update or remove `config/rag_pipeline.toml` references in RAG docs (replaced by `rag_pipeline_mcp_server.toml`)
- [ ] Update or remove `scripts/rag/models_audit.py` references in `docs/03_rag_04_03_dto-models_audit.md`
- [ ] Clarify `workflow_db_path` config key status in `docs/02_deployment.md` (Python-level default, not in agent.toml)
- [ ] Update or remove `config/common.toml`, `config/embedding.toml`, `config/tool_registry.json` references
- [ ] Update or remove `config/workflows/production.json` reference (only `default.json` exists)
- [ ] Correct file path `scripts/mcp_servers/rag_pipeline/rag_pipeline_document_manager.py` → `scripts/mcp_servers/rag_pipeline/document_manager.py`
- [ ] Correct file path `scripts/mcp_servers/github/service_pull_requests.py` → `scripts/mcp_servers/github/github_service_pull_requests.py`
- [ ] Replace undefined function names with correct names or remove references where functions no longer exist
- [ ] Update CLI command references to match `_COMMANDS` registry or remove stale entries

## Constraints
- Do not modify source code — only fix documentation references
- Preserve historical context in Migration Notes sections where appropriate
- Maintain consistency with existing documentation conventions

## Acceptance Criteria
- [ ] No references to deleted files remain without clear migration guidance
- [ ] git-mcp port number matches `config/agent.toml` (8014)
- [ ] All config file references either exist or are documented as migrated/deleted
- [ ] All function name references correspond to actual definitions
- [ ] All CLI command references correspond to registered commands
- [ ] `uv run python tools/check_docs_consistency.py --domain mcp` passes without ERROR-level findings
- [ ] `uv run python tools/check_docs_consistency.py --domain rag` passes without WARNING-level findings for missing files
- [ ] `uv run python tools/check_docs_consistency.py --domain agent` passes without WARNING-level findings for missing files
- [ ] `uv run python tools/check_docs_consistency.py --domain deployment` passes without WARNING-level findings for config keys
- [ ] `uv run python tools/check_docs_consistency.py --domain overview` passes without WARNING-level findings for config files

## Testing Expectations
Run documentation consistency checks after changes:
```bash
uv run python tools/check_docs_consistency.py --domain mcp
uv run python tools/check_docs_consistency.py --domain rag
uv run python tools/check_docs_consistency.py --domain agent
uv run python tools/check_docs_consistency.py --domain deployment
uv run python tools/check_docs_consistency.py --domain overview
```

## Documentation Impact
This issue directly affects documentation accuracy. After resolution, the documentation set should pass automated consistency checks without ERROR-level or WARNING-level findings for the categories listed above.

## Out of Scope
- Fixing the underlying source code issues (missing files, undefined functions)
- Adding new features or functionality
- Restructuring the documentation organization

## Dependencies
- None

## Unresolved Questions
- Should deleted file references be removed entirely or preserved in Migration Notes with clearer deprecation language?
- Are the undefined function references documenting historical behavior or should they be removed?
- For config files that were renamed/restructured, should we add cross-references to the new locations?

## AI Implementation Instruction
1. Run `uv run python tools/check_docs_consistency.py --domain <domain>` for each domain to confirm current state
2. For each ERROR-level finding: verify the referenced resource is truly deleted/nonexistent, then update the doc accordingly
3. For WARNING-level findings: distinguish between (a) resources that were renamed/migrated (update with new location), (b) resources that no longer exist (remove or mark deprecated), (c) typos in paths (correct the path)
4. Do NOT modify source code — only update documentation
5. After changes, re-run consistency checks to confirm no regressions
6. If any finding requires source code changes instead of doc fixes, flag as out-of-scope

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260921-193416
- **Related target files**: See Target Files or Areas above
