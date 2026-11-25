## Goal

Replace the false atomic-application and detected-but-never-applied claims with the transaction contract, the four outcome states, and the restart-required MCP rule (REQ-003, REQ-005, REQ-008, REQ-014).

## Scope
**Release unit**: R7-docs-and-manifests

## Assumptions
- Verified against current source: `### Apply Atomicity` is at `docs/23_agent/agent_07_06_cli-and-commands-hot-reload.md:47`, the atomic-application sentence at `:49`, the "detected but never applied" claim at `:55-56`, the atomicity-governs-reloadable-fields claim at `:57-58`, and the Repository Context "Reload is atomic" claim at `:62`. The classifier runs after the mutation, so the atomicity and never-applied claims are false.
- Verified against current source: the `[OK]` / `[RESTART]` / `[STARTUP-ONLY]` / `[SKIP]` / `[LIVE]` category table above the atomicity section is the vocabulary the rewritten text must keep consistent with.

## Design decisions
- The document states the four stage states and the pending behavior rather than atomicity, because the transaction is what the reader can rely on.
- The MCP paragraph states that every server-definition change requires restarting the owning process, consistent with `ADR-02-03-007` and `ADR-02-03-017`, which are not changed here.

## Alternatives considered
- N/A: keeping the atomicity wording is the claim being corrected.

## Implementation
### Target file
`docs/23_agent/agent_07_06_cli-and-commands-hot-reload.md`

### Procedure
Rewrite the atomicity section after the transaction and pending-state code lands (R7, after rows 7, 8, 19, 20, 21), then re-check the whole file against the implemented behavior.

### Method
- Replace the atomic-application and detected-but-never-applied claims with the transaction contract, the four outcome states, the pending display, and the restart-required MCP rule.
- Keep the Repository Context candidate-snapshot wording (`:62` onward) only if it still matches the implemented candidate phase.

### Details
- The `Related Documents` link to `agent_08_01` stays; the anchor name is unchanged.
- Open item for the R7 run: the Plan's Supporting Files row names `config/documentation_canonical_sources.toml` as the canonical-source registration point for the two documents this Plan edits, and neither `agent_07_06` nor `agent_08_01` is registered there today. Whether the rewritten claims need a registry entry is decided from the `check_docs_content_policy.py` output, not assumed.

## Compatibility considerations
- N/A: documentation-only change.

## Security considerations
- N/A: no configuration values are documented.

## Rollback considerations
- N/A: revert the Phase 7 commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`
- `uv run python tools/check_docs_structure.py`
- `uv run python tools/check_docs_content_policy.py`
- `uv run python tools/check_docs_consistency.py --domain agent`

## Completion criteria
- No remaining claim says a startup-only setting is applied or that reload is atomic, and the four stage states and the MCP restart rule are stated.

## Out of Scope
- The hot-reloadable scope list (row 44) and the generated artifacts (rows 45, 46).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261125-211000 | 20261125-213153 | R7 run 20261125: false atomicity and never-applied claims replaced with the four reload stages, the fixed commit order, and the pending restart display; docs quality, structure, content policy, consistency, and Japanese checks pass |
| 2 | Run the documentation checkers (`rules/tool-gates.md`) | Completed | 20261125-211000 | 20261125-213153 | R7 run 20261125: false atomicity and never-applied claims replaced with the four reload stages, the fixed commit order, and the pending restart display; docs quality, structure, content policy, consistency, and Japanese checks pass |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | The false claims the procedure targets were replaced rather than corrected in place: `### Apply Atomicity` and its atomic-application, detected-but-never-applied, and atomicity-governs-reloadable-fields sentences are gone, and the Repository Context section no longer claims "Reload is atomic". The section now states the four `ReloadStage` states and the fixed `CommitPhase` order the command actually implements | Yes | 2026-11-25 |
| 1 | The category table needed one change the procedure did not name: `[RESTART]` now names MCP server definitions specifically, while `tokenize_url` is restart-required but reported by no tag. The Responsibility Boundary states that split explicitly instead of leaving it to the table | Yes | 2026-11-25 |
| 2 | The Repository Context Reload section keeps the SHARED-003 marker: the loader is not implemented, so the section states the contract only and the checker gate passes with the marker in place | Yes | 2026-11-25 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-003, REQ-005, REQ-008, REQ-014; AC-2, AC-4, AC-5
- **Source issue**: issues/20261119-145303_cliplc005_staged-reload-transaction.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-110935_cliplc005_staged-reload-transaction.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-074359
- **Related target files**: `docs/23_agent/agent_07_06_cli-and-commands-hot-reload.md`