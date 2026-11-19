## Goal

- Create `docs/23_agent/agent_14_reference-api-subpackages-generated.md` as the generated index of the `scripts/agent/` subpackage symbols, so all 371 `agent_api` entries are published without either agent document exceeding the per-document size ceiling (`REQ-012`, `REQ-015`; `AC-009`, `AC-013`).

## Scope
**Release unit**: reference-completeness

## Assumptions

- The file is created by the generator's `--manifests` path once row 01 registers it; only the front matter above the guard comments is authored by hand.
- `tools/check_docs_structure.py` requires front matter `title`, `area`, `tags`, `related` (line 142) and a per-document size limit of `MAX_SIZE = 32768` (line 40), so the front matter is written to satisfy that checker before the first regeneration.

## Design decisions

- `D-14` (owner decision 2026-11-19, UNK-08 resolved): split the agent index across two generated documents instead of raising a size exception for one oversized one.
- Document name follows the existing generated-document convention (`agent_<seq>_<slug>-generated.md`), and the front matter `class: Reference` matches the sibling generated index so ADR-015's Generated-class rules apply unchanged.
- `related:` links `agent_12_reference-api.md` and `agent_13_reference-api-generated.md`, so the two halves of the index resolve to each other.

## Alternatives considered

- Keep all 371 entries in `agent_13_reference-api-generated.md` and add a `SIZE_EXCEPTIONS` entry (row 33): rejected by the owner - measured 54781 B against a 32768 B ceiling is a 22 KB overflow, not a rounding problem.
- Four documents, one per subpackage: rejected - `services/` alone renders 17213 B, and four documents would multiply the registration and guard bookkeeping for no size benefit.

## Implementation
### Target file
`docs/23_agent/agent_14_reference-api-subpackages-generated.md` (new)
### Procedure
1. Author the file with front matter (`title`, `area: agent`, `class: Reference`, `tags` including `generated`, `related:` naming `agent_12_reference-api.md` and `agent_13_reference-api-generated.md`) and the guard pair the generator writes between.
2. After rows 01, 02, 03, 22 land, run `uv run python tools/generate_reference_table.py --manifests` so the generator writes the subpackage block.
3. Confirm the block holds 200 entries: `workflow/` 34, `services/` 114, `commands/` 38, `shared/` 14, and no `scripts/agent/memory/` entry.
4. Confirm the file size stays under `MAX_SIZE = 32768` (measured projection 30206 B).

### Method
- Hand-authored front matter plus generator-written guarded block; the block is never edited by hand between the guard comments.

### Details
- Entry counts measured 2026-11-19 by running the generator's `_symbol_entries` per directory: top level 171, `commands/` 38, `services/` 114, `shared/` 14, `workflow/` 34, `memory/` 65 (excluded).
- Rendered block sizes measured 2026-11-19 with `render_symbol_table`: commands 4926 B, shared 1987 B, workflow 5015 B, services 17213 B - 29141 B together, and the new file's front matter plus guard comments add about 1065 B, matching `agent_13_reference-api-generated.md`'s current 1065 B outside its block.
- Guard identity, welcome line, heading, and manifest binding for this document are added in row 01 (`REFERENCE_DOC_AGENT_SUBPACKAGES`), so this row authors only the front matter and the guard comments the generator expects.
- `T-015` asserts the size ceiling and that this document plus `agent_13_reference-api-generated.md` hold every `agent_api` entry.

## Compatibility considerations

- Row 31 (`agent_12`) and row 32 (`agent_00`) register this document so a reader reaches it from the curated entry points, and row 17 records it in ADR-015's generated-document list.
- `tools/check_docs_structure.py` must be able to resolve the new basename through its index; the `related:` entries are plain basenames ending in `.md` as the checker requires.

## Security considerations

- N/A: public class and function signatures with docstring summaries.

## Rollback considerations

- Delete the file and revert the generator registration in the same commit; regeneration is the only writer.

## Validation plan

- `uv run python tools/generate_reference_table.py --manifests && git diff --exit-code registry/manifests/` — committed manifests equal regenerated output (regeneration gate: manifest freshness)
- `uv run python tools/generate_reference_table.py --check` — No drift found (drift gate: block versus manifest)
- `uv run python tools/check_docs_structure.py` — front matter, related links, and size pass for the new document (docs: documentation structure)
- `uv run pytest tests/tools/test_generate_reference_table.py -v` — under `MAX_SIZE`, every entry published exactly once (unit (T-015): ceiling and completeness)

## Completion criteria

- `AC-009`: all 371 `agent_api` entries are published across the two agent documents.
- `AC-013`: no generated Reference document exceeds `MAX_SIZE`, and no `SIZE_EXCEPTIONS` entry was added.

## Out of Scope

- Hand-editing inside the guard comments.
- Generator registration work (row 01).
- Registering the document in curated docs (rows 31, 32) or ADR-015 (row 17).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Author front matter and guard comments | Pending | — | — | hand-authored, checker-shaped |
| 2 | Regenerate so the generator writes the block | Pending | — | — | same regeneration run as rows 15, 16, 22 |
| 3 | Run `tools/check_docs_structure.py` | Pending | — | — | front matter, links, size |

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
- **Requirement ID**: `REQ-012` (agent_api covers the scripts/agent/ subpackages (workflow/, services/, commands/, shared/) so the generated API reference is complete), `REQ-015` (the generated agent API index stays within the documentation size ceiling)
- **Source issue**: issues/20261117-123014_adrchk014_contract-manifest-sources.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261119-181257_adrchk014_contract-manifest-sources.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-210556
- **Related target files**: `docs/23_agent/agent_14_reference-api-subpackages-generated.md`
