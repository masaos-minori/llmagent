## Goal

Remove the stale `embedding_dims`-config-key claim in
`docs/03_rag_05_1-configuration-reference.md` (REQ-004), per
`plans/20260826-151220_plan.md`.

## Scope

- In scope: the `embedding_dims` configuration-table row (verified at line 68 as
  of 2026-08-27) only.
- Out of scope: any other row of the same table; the file's existing
  cross-reference to `docs/02_deployment.md` section 1.4 for canonical model
  names (already correct, established by `plans/done/20260819-174858_plan.md` —
  do not remove or alter that part).

## Assumptions

- `config/agent.toml`/`config/ingester.toml` have no `embedding_dims` key
  (re-verified 2026-08-27).
- This file already partially cross-references `docs/02_deployment.md` section
  1.4 for canonical model names (per this Plan's Affected areas table note,
  "already partially cross-referenced by prior plan") — this item only needs to
  drop the literal "384" value and config-key claim, not restructure the
  existing cross-reference.

## Design decisions

- Replace "`384`" and the "float32 embedding vector dimensions (must match
  model...)" framing with a reference to the fixed code constant, per REQ-004's
  sourcing rule — keep the existing "(must match model; see [docs/02_deployment.md
  section 1.4]...)" cross-reference intact where it remains relevant (matching
  the model is still a real constraint, just not driven by a config key).

## Alternatives considered

- N/A: single table-cell correction, preserving an already-correct
  cross-reference.

## Implementation
### Target file
`docs/03_rag_05_1-configuration-reference.md`

### Procedure
1. Re-confirm the current line number immediately before editing (verified at
   line 68 as of 2026-08-27).
2. Rewrite the `embedding_dims` row per Method/Details, preserving the existing
   `docs/02_deployment.md` section 1.4 cross-reference.
3. Run `.venv/bin/python3 tools/check_docs_consistency.py --domain rag` and
   confirm no new warning/error.

### Method
Direct text edit (Edit tool) — one table row.

### Details
Current row (verified 2026-08-27, line 68):
```
| `embedding_dims` | `384` | float32 embedding vector dimensions (must match model; see [docs/02_deployment.md section 1.4](./02_deployment.md#14-llm--How to get models) for canonical model names) |
```
Replace with:
```
| Embedding dimension | Fixed code-level constant | `scripts/db/store_protocols.py::get_embedding_dims()` — must match the actual deployed embedding model; see [docs/02_deployment.md section 1.4](./02_deployment.md#14-llm--How to get models) for canonical model names |
```
Verify the exact link anchor text (`#14-llm--How to get models`) still matches
`docs/02_deployment.md`'s actual current heading/anchor before finalizing —
re-use the existing link text verbatim from this same row rather than
retyping it, to avoid introducing a typo in the anchor.

## Compatibility considerations

- Documentation-only; no runtime behavior, config schema, or public interface
  is affected.

## Security considerations

- N/A: no security-relevant content.

## Rollback considerations

- Single-row text revert via `git diff`/`git checkout -- <path>`; independent
  of the other 14 target files in this Plan's pass.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/03_rag_05_1-configuration-reference.md` | Manual diff | `git diff <path>` | No config-key claim remains; existing cross-reference preserved |
| `docs/03_rag_05_1-configuration-reference.md` | Doc consistency check | `.venv/bin/python3 tools/check_docs_consistency.py --domain rag` | No new warning/error beyond baseline |

## Completion criteria

- The row no longer states `embedding_dims` is a configurable key defaulting to
  `384`.
- The existing `docs/02_deployment.md` section 1.4 cross-reference is
  preserved.

## Out of scope

- Any other row of the same table.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-confirm line number | Pending | — | — | |
| 2 | Rewrite the `embedding_dims` row | Pending | — | — | |
| 3 | Run `check_docs_consistency.py --domain rag` | Pending | — | — | |

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
- **Requirement ID**: REQ-004
- **Source issue**: `issues/20260821_10_issue.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260826-151220_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260827-112854
- **Related target files**: `docs/03_rag_05_1-configuration-reference.md`
