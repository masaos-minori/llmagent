## Goal

Refresh the generated API reference table so the removed `RAGConfig` row disappears, using the generator rather than hand-editing (REQ-001; Documentation Impact; ADR-015 INV-01).

## Scope
**Release unit**: N/A: documentation update (Phase 5)

## Assumptions
- The guarded `AUTO-GENERATED` block must not be edited by hand; only `tools/generate_reference_table.py` writes it.
- The generator reads source symbols, so this row is only valid after Plan row 1 removes `RAGConfig`.

## Design decisions
- Run the generator with `--check` first to confirm the drift, then regenerate; no manual wording is added inside the guarded block.

## Alternatives considered
- Hand-edit the row out of the table: rejected by ADR-015 INV-01, which makes the generated block the single source for these rows.

## Implementation
### Target file
`docs/23_agent/agent_13_reference-api-generated.md`
### Procedure
- Run `uv run python tools/generate_reference_table.py --check` to confirm the `RAGConfig` row is stale.
- Regenerate the guarded block; confirm `MemoryConfig`'s new field appears if the generator lists fields.
- Do not edit anything outside the guarded block.
### Method
- Tool-driven regeneration only.
### Details
- Verified 2026-11-21: line 46 currently lists `class RAGConfig`; the row is inside the guarded block, so the change must come from the generator.

## Compatibility considerations
- Other generated blocks in the same file are unaffected.

## Security considerations
- N/A: documentation only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/generate_reference_table.py --check`
- `uv run python tools/check_docs_quality.py`
- `uv run python tools/check_docs_structure.py docs/23_agent/agent_13_reference-api-generated.md`

## Completion criteria
- `--check` passes against the source after Plan row 1 lands; no `RAGConfig` row remains in the generated block.

## Out of Scope
- The prose documents (Plan rows 27-30), the class definition itself (Plan row 1).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|---|---|---|---|---|---|
| 1 | Implement the change described in Implementation > Procedure/Method | Completed | 2026-11-22 | 2026-11-22 | Ran --check first: drift in registry/manifests/agent_api.yaml, memory_api.yaml and config_ownership.yaml (RAGConfig row removed, memory_embed_url added, config ownership updated). Regenerated with --manifests, which rewrote only the guarded blocks of agent_13, agent_14 and agent_11_04; nothing outside the guarded blocks was edited. |
| 2 | Add or update tests per Validation plan | Completed | 2026-11-22 | 2026-11-22 | N/A: documentation row; the generator check is the verification. Gated: same as step 1 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-22 | 2026-11-22 | generate_reference_table.py --check now reports no drift; check_docs_structure passes on agent_13 and no RAGConfig row remains in the generated block. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 2026-11-22 | 2026-11-22 | Gated: same - sibling documentation rows are separate procedure documents |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|---|---|---|---|
| 1 | Cannot run before Plan row 1 removes `RAGConfig`; the generator output depends on that change | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---|---|---|---|---|---|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001 (documentation impact)
- **Source issue**: issues/20261120-114212_agentcfg004_config-ownership-split.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-140444_agentcfg004_config-ownership-split.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-144837
- **Related target files**: `docs/23_agent/agent_13_reference-api-generated.md`
