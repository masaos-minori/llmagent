## Goal

Remove the stale `embedding_dims`-config-key claim in
`docs/00_security_01_architecture-and-trust-boundaries.md` (REQ-004 — added by
this plan-to-implementation-procedure's own adversarial verification,
2026-08-27), per `plans/20260826-151220_plan.md`.

## Scope

- In scope: the "Embedding dimension mismatch" row of the "RAG failure
  behavior" table (verified at line 206 as of 2026-08-27) only.
- Out of scope: every other row of the same table (Embedding API down, Vector
  store corruption, FTS index desync, Orphan vector rows, Crawler timeout —
  all unrelated, unaffected); any other content in this document.

## Assumptions

- This file was found by re-running this Plan's own Phase 1 preparation grep
  (`rg -rl "embedding_dims|memory_embed_dim" docs/`) during
  plan-to-implementation-procedure adversarial verification (2026-08-27) — it
  was NOT in this Plan's original 11-file REQ-004 list. The Plan document has
  been updated to include this file; this procedure implements that addition.
- `config/agent.toml` has no `embedding_dims` key (re-verified 2026-08-27) —
  the "Verify embedding_dims config" recovery instruction is actionable advice
  pointing at a nonexistent config key.

## Design decisions

- Replace "Verify embedding_dims config" with recovery guidance pointing at
  the actual, fixed source of truth
  (`scripts/db/store_protocols.py::get_embedding_dims()`) — per REQ-004's
  sourcing rule, applied consistently with the other twelve files in this
  Plan's pass.

## Alternatives considered

- N/A: single table-cell correction, following the same pattern already
  applied to the other twelve REQ-004 files.

## Implementation
### Target file
`docs/00_security_01_architecture-and-trust-boundaries.md`

### Procedure
1. Re-confirm the current line number immediately before editing (verified at
   line 206 as of 2026-08-27).
2. Rewrite the "Embedding dimension mismatch" row's Recovery column per
   Method/Details.
3. Run `.venv/bin/python3 tools/check_docs_consistency.py --domain overview`
   (or the domain this file actually falls under per `docs/00_index.md`'s task
   mapping — verify before running, since a `00_security_*` file may not map
   to `overview`) and confirm no new warning/error.

### Method
Direct text edit (Edit tool) — one table cell.

### Details
Current row (verified 2026-08-27, line 206):
```
| Embedding dimension mismatch | Chunk skipped, WARNING logged | Verify embedding_dims config |
```
Replace with:
```
| Embedding dimension mismatch | Chunk skipped, WARNING logged | Verify the embedding model's output matches `scripts/db/store_protocols.py::get_embedding_dims()` (a fixed code-level constant, not a config key) |
```

## Compatibility considerations

- Documentation-only; no runtime behavior, config schema, or public interface
  is affected.

## Security considerations

- N/A: no security-relevant content — this table describes an operational
  recovery procedure, not a trust-boundary claim; the fix does not change any
  security-relevant statement elsewhere in this security-focused document.

## Rollback considerations

- Single-cell text revert via `git diff`/`git checkout -- <path>`; independent
  of the other 14 target files in this Plan's pass.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/00_security_01_architecture-and-trust-boundaries.md` | Manual diff | `git diff <path>` | No config-key claim remains |
| `docs/00_security_01_architecture-and-trust-boundaries.md` | Doc consistency check | `.venv/bin/python3 tools/check_docs_consistency.py --domain <correct domain>` (verify domain mapping first) | No new warning/error beyond baseline |

## Completion criteria

- The "Embedding dimension mismatch" row no longer instructs verifying an
  `embedding_dims` config key.

## Out of scope

- Every other row of the "RAG failure behavior" table.
- Any other content in this document.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-confirm line number | Pending | — | — | |
| 2 | Rewrite the Recovery column | Pending | — | — | |
| 3 | Run `check_docs_consistency.py` (correct domain) | Pending | — | — | |

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
- **Related target files**: `docs/00_security_01_architecture-and-trust-boundaries.md`
