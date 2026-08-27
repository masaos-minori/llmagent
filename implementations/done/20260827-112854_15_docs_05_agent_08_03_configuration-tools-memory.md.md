## Goal

Remove the fabricated `memory_embed_dim` config-key reference in
`docs/05_agent_08_03_configuration-tools-memory.md` (REQ-004 — added by this
plan-to-implementation-procedure's own adversarial verification, 2026-08-27),
per `plans/20260826-151220_plan.md`.

## Scope

- In scope: the `memory_embed_dim` bullet in the "Embedding Related" subsection
  (verified at line 98 as of 2026-08-27) only.
- Out of scope: the other three bullets in the same subsection
  (`memory_embed_enabled`, `memory_embed_timeout_sec`, `memory_local_only` —
  all genuinely real `AgentConfig.memory` config keys, unaffected); any other
  content in this document.

## Assumptions

- This file was found by re-running this Plan's own Phase 1 preparation grep
  (`rg -rl "embedding_dims|memory_embed_dim" docs/`) during
  plan-to-implementation-procedure adversarial verification (2026-08-27) — it
  was NOT in this Plan's original 11-file REQ-004 list. The Plan document has
  been updated to include this file; this procedure implements that addition.
- `memory_embed_dim` does not exist anywhere in `scripts/` (re-verified
  2026-08-27) — this bullet fabricates it as a real config key, listed
  alongside three genuinely-real sibling keys in the same subsection, which
  makes this fabrication particularly easy for a reader to miss.
- `scripts/agent/factory.py:382` (`MemoryStore(embed_dim=get_embedding_dims())`,
  re-verified 2026-08-27 during seq 13's investigation in this same pass) is
  the actual source of the embedding dimension used by `MemoryStore` — not a
  config field.

## Design decisions

- Remove the `memory_embed_dim` bullet entirely (it is fabricated, not merely
  stale-valued) — do not renumber "384" to a new value, since no such field
  exists.
- Add, in its place or as a brief trailing note in the same subsection, a
  statement that the embedding dimension used by memory search is a fixed
  code-level constant (`scripts/db/store_protocols.py::get_embedding_dims()`),
  not a `memory_*` config key — so a reader does not conclude the dimension is
  simply undocumented rather than non-configurable.

## Alternatives considered

- Leaving the bullet in place but correcting its value was considered and
  rejected — the field itself does not exist on `AgentConfig.memory`;
  correcting only the number would still leave the false claim that this is a
  real, settable config key.

## Implementation
### Target file
`docs/05_agent_08_03_configuration-tools-memory.md`

### Procedure
1. Re-confirm the current line number immediately before editing (verified at
   line 98 as of 2026-08-27).
2. Remove the `memory_embed_dim` bullet.
3. Add a brief replacement note per Method/Details.
4. Cross-check wording against seq 13's (`05_agent_12_03`) parallel correction
   for the same fabricated field, for consistency across the two docs.
5. Run `.venv/bin/python3 tools/check_docs_consistency.py --domain agent` and
   confirm no new warning/error.

### Method
Direct text edit (Edit tool) — remove one bullet, add one replacement
sentence.

### Details
Current subsection (verified 2026-08-27, lines 95-99):
```
#### Embedding Related

- `memory_embed_enabled`: Enables embedding + KNN for memory search.
- `memory_embed_dim`: Embedding dimension (must match vec0 schema).
- `memory_embed_timeout_sec`: Timeout for embedding HTTP calls.
- `memory_local_only`: Rejects non-loopback `embed_url` at startup.
```
Remove the `memory_embed_dim` bullet, replacing it with a non-bulleted note (to
distinguish it from the three genuinely-configurable sibling keys):
```
#### Embedding Related

- `memory_embed_enabled`: Enables embedding + KNN for memory search.
- `memory_embed_timeout_sec`: Timeout for embedding HTTP calls.
- `memory_local_only`: Rejects non-loopback `embed_url` at startup.

The embedding dimension itself is not a config key — it is a fixed code-level
constant (`scripts/db/store_protocols.py::get_embedding_dims()`), used
identically by `MemoryStore` (`agent/factory.py`) and the RAG pipeline.
```

## Compatibility considerations

- Documentation-only; no runtime behavior, config schema, or public interface
  is affected.

## Security considerations

- N/A: no security-relevant content.

## Rollback considerations

- Single-bullet-plus-note text revert via `git diff`/`git checkout -- <path>`;
  should be cross-checked against seq 13 (`05_agent_12_03`)'s parallel
  correction for consistency of wording, though each file is independently
  revertable.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/05_agent_08_03_configuration-tools-memory.md` | Manual diff | `git diff <path>` | No `memory_embed_dim` bullet remains; the other three "Embedding Related" bullets unchanged |
| `docs/05_agent_08_03_configuration-tools-memory.md` | Doc consistency check | `.venv/bin/python3 tools/check_docs_consistency.py --domain agent` | No new warning/error beyond baseline |

## Completion criteria

- No statement remains that `memory_embed_dim` is a configurable
  `AgentConfig.memory` key.
- The three genuinely-real sibling keys remain documented, unchanged.

## Out of scope

- `memory_embed_enabled`, `memory_embed_timeout_sec`, `memory_local_only`.
- Any other content in this document.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-confirm line number | Completed | — | — | Verified at line 98 |
| 2 | Remove the `memory_embed_dim` bullet | Completed | — | — | Removed fabricated config key |
| 3 | Add replacement note | Completed | — | — | Added code-level constant reference |
| 4 | Cross-check wording against seq 13 | Completed | — | — | Consistent with seq 13 correction |
| 5 | Run `check_docs_consistency.py --domain agent` | Completed | — | — | No new warnings |

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
- **Related target files**: `docs/05_agent_08_03_configuration-tools-memory.md`
