## Goal

- Commit the regenerated `agent_13_reference-api-generated.md` guarded block: the top-level `agent_api` entries with the corrected welcome line, kept inside the per-document size ceiling (`REQ-012`; `AC-009`, `AC-013`).

## Scope
**Release unit**: reference-completeness

## Assumptions

- The file is Generated-class: the only permitted change is committing what `tools/generate_reference_table.py --manifests` writes.
- Row 01 is what makes the block change (welcome line and top-level-only scope); nothing here edits the generator.

## Design decisions

- `D-14`: this document keeps the 171 top-level entries; the 200 subpackage entries move to `docs/23_agent/agent_14_reference-api-subpackages-generated.md` (row 30), so neither document needs a size exception.

## Alternatives considered

- Keep all 371 entries here and register a `SIZE_EXCEPTIONS` entry: rejected by the owner (`D-14`, UNK-08) - measured 54781 B against a 32768 B ceiling.

## Implementation
### Target file
`docs/23_agent/agent_13_reference-api-generated.md`
### Procedure
1. After rows 01, 02, 03 land, run `uv run python tools/generate_reference_table.py --manifests` and commit the rewritten guarded block.
2. Verify the welcome line inside the guard now describes the top-level scan, and that the block holds the 171 top-level entries only.
3. Confirm the whole file stays under `MAX_SIZE = 32768`.

### Method
- Regeneration only - never hand-edit between the guard comments; the curated front matter and tail sections are not touched by the generator.

### Details
- Measured 2026-11-19: file 25835 B with a 24770 B guarded block holding 171 entries; 1065 B sits outside the block.
- Current welcome line (line 32) says `scripts/agent/*.py` top-level public classes and functions; after row 01 it names the same scope while the subpackage symbols move to the new document.

## Compatibility considerations

- Row 31 and row 32 register the new sibling document, so a reader arriving through `agent_12` or the guide reaches both indexes.
- `tools/check_docs_structure.py` enforces front matter, tail sections, related-link coverage, and size; the `related:` link to `agent_12_reference-api.md` stays.

## Security considerations

- N/A: symbol signatures only.

## Rollback considerations

- Revert the commit; regeneration reproduces the previous block from the previous sources.

## Validation plan

- `uv run python tools/generate_reference_table.py --manifests && git diff --exit-code registry/manifests/` — committed manifests equal regenerated output (regeneration gate: manifest freshness)
- `uv run python tools/generate_reference_table.py --check` — No drift found (drift gate: block versus manifest)
- `uv run python tools/check_docs_structure.py && uv run python tools/check_docs_consistency.py --domain agent` — no size or stale finding (docs: documentation gates)

## Completion criteria

- `AC-013`: no generated Reference document exceeds the size ceiling, and this file plus row 30 hold every `agent_api` entry.

## Out of Scope

- Any hand-edit inside the guard comments.
- Generator changes (row 01).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Regenerate and commit the guarded block | Completed | 20261119-232759 | 20261119-232759 | generator writes the block guarded block regenerated with 171 top-level entries, 25931 B; check_docs_structure and the agent docs gates pass |
| 2 | Run `tools/check_docs_structure.py` and the agent docs gates | Completed | 20261119-232759 | 20261119-232759 | no size finding guarded block regenerated with 171 top-level entries, 25931 B; check_docs_structure and the agent docs gates pass |

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
- **Requirement ID**: `REQ-012` (agent_api covers the scripts/agent/ subpackages (workflow/, services/, commands/, shared/) so the generated API reference is complete)
- **Source issue**: issues/20261117-123014_adrchk014_contract-manifest-sources.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261119-181257_adrchk014_contract-manifest-sources.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-210556
- **Related target files**: `docs/23_agent/agent_13_reference-api-generated.md`