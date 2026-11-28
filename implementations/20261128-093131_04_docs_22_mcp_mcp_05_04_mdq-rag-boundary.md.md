## Goal

State what the boundary actually proves now: three import-linter contracts for the enforced directions, an AST call check for connection creation, one direction that remains a convention, and the limit of static detection (`REQ-004`, `AC-4`).

## Scope
**Release unit**: N/A: not part of a release unit

- The Data Ownership paragraph (line 69) names the mechanism behind each claim.
- The Agent Access Patterns item 3 (line 79) states the AST call check instead of a string scan, and adds the limit for dynamic access.
- The RAG and Agent Responsibility Boundary note (line 86) keeps `agent → rag` as a convention and distinguishes it from the enforced directions.
- The test citations at lines 69, 78, 79, and 108 name the tests that carry each claim.

## Assumptions

- Verified at current HEAD: lines 69, 78, 79, 86, and 108 are the lines that cite `tests/mcp_servers/mdq/test_mdq_rag_boundary.py`, and line 79 states the scan is a source-level guard rather than a runtime guarantee — the issue's claim held.
- The test names cited here are not renamed by row 3, so the citations keep resolving; only the mechanism wording changes.
- Content policy (`skills/DESIGN.md`): the existing single symbol references in the touched sentences stay, because they name the guard and the mechanism, not an index; no file tree, symbol table, or implementation-location mapping is added.
- The enforcement mechanism itself lives in `docs/22_mcp/mcp_05_05_mdq-enforcement-and-lockdown.md` (row 5); this document states the enforced directions and the limits, and points to that document for the exception policy, so one claim is not stated twice.
- Front Matter, `Keywords`, and the `related:` list are unchanged; the file already passes `tools/check_docs_structure.py` as it stands.

## Design decisions

- Write each claim as what proves it: contracts prove import direction, the AST check proves connection creation, nothing proves dynamic access, and a convention proves nothing. That is what makes `AC-4` checkable.
- Keep the claim about the agent reaching the databases through tool calls unchanged; only the enforcement sentence changes.

## Alternatives considered

- Add a table of enforced directions: rejected, the document already carries the claim in prose, and a table of directions would read as an implementation-location mapping.

## Implementation
### Target file
`docs/22_mcp/mcp_05_04_mdq-rag-boundary.md`

### Procedure
1. In Data Ownership, state that import direction is enforced by the three contracts (`mdq-no-rag`, `rag_pipeline-no-mdq`, `agent-no-mdq`) and that connection creation is enforced by the AST call check outside the modules that own a database.
2. In Agent Access Patterns item 3, replace the string-scan sentence with the AST decision and add that dynamic access through `importlib` or `getattr` is not detected.
3. In the RAG and Agent Responsibility Boundary note, keep `agent → rag` as a convention and say it is not one of the enforced directions.
4. Update the test citations to the tests that carry each claim, keeping the existing names.

### Method

- Each change is one sentence or one clause inside an existing paragraph; no section is added or restructured.

### Details

- The database-owning modules are named as a set in prose, not as a table, and the exception records themselves are described in the enforcement document.

## Compatibility considerations

- `tools/check_docs_consistency.py --domain mcp` cross-checks symbol references against `scripts/`; the contract names stated here must match `.importlinter` after row 1 lands, so the document is updated in the same change as the contracts.
- The enforcement document cites this document's claims, so the exception policy is stated once, in that document.

## Security considerations

- `N/A: documentation only.`

## Rollback considerations

- `N/A: revert the commit.`

## Validation plan

- `uv run python tools/check_docs_content_policy.py`
- `uv run python tools/check_docs_structure.py docs/22_mcp/mcp_05_04_mdq-rag-boundary.md`
- `uv run python tools/check_docs_quality.py`
- `uv run python tools/check_docs_consistency.py --domain mcp`
- `uv run python tools/generate_reference_table.py --check`
- Full sequence per `rules/toolchain.md`.

## Completion criteria

- Each claim names the mechanism that proves it, and each claim matches what the contract or the test actually enforces (`AC-4`).

## Out of Scope

- The exception-record policy (`docs/22_mcp/mcp_05_05_mdq-enforcement-and-lockdown.md`, row 5).
- The contracts and the AST helper (rows 1, 2).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Plan Phase 5 |
| 2 | Run the documentation checkers named in `rules/tool-gates.md` | Pending | — | — | The "Add or update tests" step does not apply to a docs-only row |

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
- **Requirement ID**: REQ-004, AC-4
- **Source issue**: `issues/20261119-142131_mdqmcp009_mdq-rag-boundary-rules.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-192529_mdqmcp009_mdq-rag-boundary-rules.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261128-093131
- **Related target files**: `docs/22_mcp/mcp_05_04_mdq-rag-boundary.md`
