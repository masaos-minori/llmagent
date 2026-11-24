## Goal
Retire the JSONL store, import, rebuild, pin, and manual-write modules in the module reference and use Episodic Memory Layer wording (REQ-007).

## Scope
**Release unit**: agent-memory-docs

- Edits only `docs/23_agent/agent_11_03_memory-module-reference.md`; applied with the other documents of the release unit because the Agent documents cross-link and are validated together.

## Assumptions
- The amended ADR-008 (Decision Details 22 to 25, INV-20 to INV-22) is the contract; the document links to it instead of restating it.
- Where the code or policy differs, the document cites SHARED-003 (code and CLI still match the old model; Repository Context, its diagnostics, and its reload are not implemented) or SHARED-004 (lifecycle policies undecided); no `Needs Confirmation` marker is added, because unregistered markers fail `tools/check_needs_confirmation_inventory.py`.
- Before removing or renaming a heading, search for links to its anchor (`rg -n "#<anchor>" docs`) and keep or update them in the same edit set.
- Names of keys, fields, categories, and authority values that no approved design or code defines are not written.

## Design decisions
- Keep the module reference structure; replace the retired modules' descriptions with one "Retired by ADR-008" list that names them without API descriptions.

## Alternatives considered
N/A: documentation only; the Plan fixes the approach.

## Implementation
### Target file
`docs/23_agent/agent_11_03_memory-module-reference.md`

### Procedure
1. Purpose and Design Intent: change "memory layer" to "Episodic Memory Layer" where it names the persistent layer; remove "compatible with both JSONL and SQLite" and the append-only archiving wording.
2. Retrieval and Injection: in the Default `InjectionPolicy` bullet remove the semantic count and importance threshold, keeping the episodic count and the snippet length.
3. Extraction and Facade: remove the `JsonlMemoryStore` bullet, the JSONL failure bullet, and the manual-write deduplication clause.
4. Core and Store operational notes: replace the `/memory prune` and per-memory `delete` retention statement with internal retention (policy undecided, SHARED-004).
5. Extraction and Facade operational notes: replace the `/memory status` line with the diagnostics owner (`/stats`, SHARED-003).
6. Ops and Scoring: remove the `import_from_jsonl()` bullet; keep the index-rebuild bullet.
7. Add "Retired by ADR-008": list the JSONL store, JSONL import, rebuild, pin, and manual-write modules (`jsonl_store.py`, `import_ops.py`, `rebuild_ops.py`, `pin_ops.py`, `write_ops.py`) as removal-pending; they exist in code only until SHARED-003 is resolved.

### Method
- Use the Edit tool; locate with `rg -n -i "jsonl|pin|import_from|manual|semantic|/memory" docs/23_agent/agent_11_03_memory-module-reference.md`.

### Details
- Do not edit the generated memory reference document or the manifests; they follow the code.
- The retired list gives names only, no signatures.

## Compatibility considerations
N/A: documentation only.

## Security considerations
N/A: no security-relevant change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_consistency.py --domain agent`; `uv run python tools/generate_reference_table.py --check`.
- `uv run python tools/check_docs_quality.py` and `uv run python tools/check_docs_content_policy.py`.

## Completion criteria
- The JSONL, import, pin, manual-write, rebuild, and `/memory` APIs are no longer described as supported; the retired list cites SHARED-003; the generated reference and manifests show no drift.

## Out of Scope
- Any other file, code, configuration, the generated memory reference, and the API manifests.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the document per Implementation | Pending | — | — | |
| 2 | Run the documentation checkers per Validation plan | Pending | — | — | Release unit agent-memory-docs |

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
- **Requirement ID**: REQ-007 (module reference)
- **Source issue**: issues/20261124-093929_adrdoc003_agent-memory-docs-episodic.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-103155_adrdoc003_agent-memory-docs-episodic.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-103504
- **Related target files**: `docs/23_agent/agent_11_03_memory-module-reference.md`
