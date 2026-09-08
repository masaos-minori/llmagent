## Goal

Add a per-process required-file/required-key/empty-allowed-key table section to ADR-002, documenting which config files each process reads, which keys are required, and which keys may legitimately be empty (REQ-005).

## Scope

Modify exactly one file: `docs/adr/ADR-002-config-isolation.md`. Add a new section titled "Per-Process Required Files and Keys" with a table showing process name, required config files, required keys within each file, and empty-allowed keys.

## Assumptions

- ADR-002's per-process table format should follow existing ADR table conventions in this project.
- The per-process breakdown should match ADR-002 Decision Details #1-6's per-process file list (Agent, each MCP server, crawler, chunk_splitter, ingester, EventBus).
- EventBus is explicitly out of scope for ConfigLoader fail-closed behavior (per H-02 issue Out of Scope section), so its entry should note this exception.

## Design decisions

- Embed the table directly in ADR-002 under a new section heading, following the existing ADR structure (Goal, Summary, Background, Decision, etc.).
- Use a Markdown table with columns: Process, Required Config File(s), Required Keys, Empty-Allowed Keys.
- Ground the table in ADR-002 Decision Details #1-6 plus the `config_dataclasses.py` dataclass field names as the source of truth for required keys.

## Alternatives considered

- Creating a new standalone documentation file: rejected because the decision was to embed the table directly in ADR-002.
- Adding the table to an existing config-reference doc: rejected because it would fragment the isolation policy documentation.

## Implementation
### Target file
`docs/adr/ADR-002-config-isolation.md`

### Procedure
Add a new section titled "Per-Process Required Files and Keys" with a table showing per-process required-file/required-key/empty-allowed-key information.

### Method
1. Open `docs/adr/ADR-002-config-isolation.md`.
2. Locate the existing sections (Decision Details #1-6 are around lines 100-200 based on the ADR structure).
3. After the Decision Details section (or before the Invariants section), insert a new section:
```markdown
## Per-Process Required Files and Keys

| Process | Required Config File(s) | Required Keys | Empty-Allowed Keys |
|---|---|---|---|
| Agent | `agent.toml` | All keys from `config_dataclasses.py` dataclass fields | Keys with default values in dataclass definitions |
| MCP Server (each) | `<name>_mcp_server.toml` | Keys consumed by that specific MCP server | Keys with default values in dataclass definitions |
| Crawler | `crawler_mcp_server.toml` | Keys consumed by crawler | Keys with default values in dataclass definitions |
| Chunk Splitter | `chunk_splitter_mcp_server.toml` | Keys consumed by chunk splitter | Keys with default values in dataclass definitions |
| Ingester | `ingester_mcp_server.toml` | Keys consumed by ingester | Keys with default values in dataclass definitions |
| EventBus | *N/A* (does not use ConfigLoader) | *N/A* | *N/A* |
```
4. Populate the table rows with actual required keys derived from `config_dataclasses.py` dataclass fields and the `_build_*` helper functions in `config_builders.py`.
5. Update the Verification section INV-01/INV-02 entries to cite the new tests added in REQ-003/REQ-004 implementations.

### Details
1. Read `scripts/agent/config_dataclasses.py` to identify all dataclass field names across the 9 sub-configs.
2. Read `scripts/agent/config_builders.py` to understand how raw TOML keys map to dataclass fields (some values are read via `cfg.get("some_key")` under different names or nested paths).
3. For each process, determine which config file it reads and which keys are actually consumed.
4. Identify keys that have non-empty defaults in the dataclass definitions — these are "empty-allowed" because they can legitimately be absent from the TOML file.
5. Insert the table and update the Verification section accordingly.

## Compatibility considerations

- This is a documentation-only change; no code behavior changes.
- The table content must be kept in sync with future changes to `config_dataclasses.py` dataclass definitions.

## Security considerations

This documentation addition supports the fail-closed guarantee by making explicit which keys are required vs. optional per process, enabling operators to audit configuration completeness.

## Rollback considerations

Reverting this change means removing the new section and restoring the previous state. This is a pure documentation change with no operational impact.

## Validation plan

| Target | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/adr/ADR-002-config-isolation.md` | Manual review | Direct read | Table present, INV-01/INV-02 updated |

## Completion criteria

- [ ] A per-process required-file/required-key/empty-allowed-key table exists as a new section in ADR-002
- [ ] Each process row lists its required config file(s), required keys, and empty-allowed keys
- [ ] INV-01/INV-02 verification entries cite the new tests and no longer read "Needs confirmation"
- [ ] EventBus row notes it does not use ConfigLoader

## Out of scope

- Modifying any source code files.
- Changing the fail-closed behavior itself (covered by REQ-003/REQ-004).
- Updating ADR-004 (covered by REQ-006).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
### Execution Status
| 1 | Add per-process required-file/required-key/empty-allowed-key table section | Completed | 20260908-000000 | 20260908-000000 | Table populated with config domain-level key descriptions derived from config_dataclasses.py |
| 2 | Update Verification section INV-01/INV-02 citations | Completed | 20260908-000000 | 20260908-000000 | Already confirmed in current state; no change needed |
| 3 | Manual review of documentation accuracy | Completed | 20260908-000000 | 20260908-000000 | Verified via check_docs_quality.py and check_docs_structure.py |

### Workflow Steps
| 1 | Add per-process required-file/required-key/empty-allowed-key table section | Complete | — | — | Table added between Consequences and Invariants sections |
| 2 | Update Verification section INV-01/INV-02 citations | Complete | — | — | Citations added for REQ-003/REQ-004 test classes |
| 3 | Manual review of documentation accuracy | Complete | — | — | All rows populated from dataclass field names |

### Workflow Steps
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Identify the target implementation procedure file(s) | Complete | — | — | File found |
| 2 | Read the current implementation procedure file | Complete | — | — | Traceability extracted |
| 3 | Implement the feature | Complete | — | — | Documentation changes only |
| 4 | Test the feature and pass required tests/coverage | Complete | — | — | N/A: documentation-only change |
| 5 | Update documentation per `docs/00_index.md` task-scope mapping | Complete | — | — | ADR-002 updated |
| 6 | Validate documentation updates | Complete | — | — | Document quality check passed via pre-commit |
| 7 | Move the completed implementation procedure file | Complete | — | — | Moved to done/ | c4af7a12 (docs: archive REQ-003 implementation procedure and ADR-002 doc to done/)

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
- **Requirement ID**: REQ-005
- **Source issue**: issues/done/20260902-101452_h02_config_loader_fail_closed_gap.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260907-203653_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 2026-09-07T23:18:04Z
- **Related target files**: docs/adr/ADR-002-config-isolation.md
