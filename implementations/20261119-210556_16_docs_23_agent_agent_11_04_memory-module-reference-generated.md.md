## Goal

- Commit the regenerated memory reference block after the `memory` welcome line names its manifest, so the three symbol-reference documents describe their sources the same way (`REQ-009`; `AC-006`).

## Scope
**Release unit**: reference-completeness

## Assumptions

- Generated-class file: only the regenerated block changes.
- UNK-06 plan default: name `registry/manifests/memory_api.yaml` in the welcome line.

## Design decisions

- `D-09`: the welcome line states the manifest and the scan the block was rendered from, mirroring `agent` and `eventbus`.

## Alternatives considered

- Drop manifest naming from `agent` and `eventbus` instead: rejected by the UNK-06 plan default - the manifest is the artifact the block is rendered from.

## Implementation
### Target file
`docs/23_agent/agent_11_04_memory-module-reference-generated.md`
### Procedure
1. After row 01 changes `DOMAIN_WELCOME_LINES["memory"]`, run `uv run python tools/generate_reference_table.py --manifests` and commit the rewritten block.
2. Confirm the file stays under the per-document ceiling: it is 32022 B today, 746 B below `MAX_SIZE = 32768`, so the welcome-line change must stay a single clause.

### Method
- Regeneration only; front matter and tail sections untouched.

### Details
- Current welcome line at `docs/23_agent/agent_11_04_memory-module-reference-generated.md:37` names `scripts/agent/memory/*.py` and no manifest.
- Measured 2026-11-19: the memory scan holds 24 files and 65 symbols; `agent_api` excludes them (ASM-06), so no entry moves between the two documents.

## Compatibility considerations

- Row 28 regenerates `registry/manifests/memory_api.yaml` in the same commit; the block is rendered from that committed manifest.

## Security considerations

- N/A: symbol signatures only.

## Rollback considerations

- Revert the commit.

## Validation plan

- `uv run python tools/generate_reference_table.py --check` — No drift found (drift gate: block versus manifest)
- `uv run python tools/check_docs_structure.py && uv run python tools/check_docs_quality.py` — no size or stale finding (docs: documentation gates)

## Completion criteria

- The memory block's welcome line names `registry/manifests/memory_api.yaml` and the file stays under the size ceiling.

## Out of Scope

- Any hand-edit inside the guard comments.
- Moving memory symbols into `agent_api` (ASM-06).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Regenerate and commit the guarded block | Pending | — | — | generator writes the block |
| 2 | Run `tools/check_docs_structure.py` | Pending | — | — | size headroom confirmed |

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
- **Requirement ID**: `REQ-009` (every manifest's sources list names exactly the files and directories its builder reads)
- **Source issue**: issues/20261117-123014_adrchk014_contract-manifest-sources.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261119-181257_adrchk014_contract-manifest-sources.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-210556
- **Related target files**: `docs/23_agent/agent_11_04_memory-module-reference-generated.md`
