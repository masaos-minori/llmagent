## Goal

Remove the fabricated `AgentConfig.memory.memory_embed_dim` field reference in
`docs/05_agent_12_03_memory-module-ref-core-and-store.md` (REQ-004), per
`plans/20260826-151220_plan.md`.

## Scope

- In scope: the `embed_dim` sentence (verified at line 45 as of 2026-08-27)
  only.
- Out of scope: any other content in this document.

## Assumptions

- `AgentConfig.memory` has no `memory_embed_dim` field — re-verified 2026-08-27,
  `memory_embed_dim` does not appear anywhere in `scripts/`. This is one of the
  two fabricated-field items this Plan specifically calls out (the other being
  `DbConfig.embedding_dims`, seq 07 in this same pass).
- **Confirmed (plan-to-implementation-procedure verification, 2026-08-27)**:
  `scripts/agent/factory.py:382` calls `MemoryStore(embed_dim=get_embedding_dims())`
  — `embed_dim` is sourced directly from
  `scripts/db/store_protocols.py::get_embedding_dims()`, not from any
  `AgentConfig.memory` field. This resolves step 2 of this item's own Procedure
  without further investigation needed at implementation time.
- **Additional finding (plan-to-implementation-procedure adversarial
  verification, 2026-08-27)**: the same fabricated `memory_embed_dim` name also
  appears in `docs/05_agent_08_03_configuration-tools-memory.md` (line 98,
  listed alongside genuinely-real `memory_*` config keys) — a separate target
  file added to this Plan's REQ-004 scope, seq 15 in this same pass. Both
  occurrences must be corrected; this item covers only this file's occurrence.

## Design decisions

- Remove the false claim that `embed_dim` is passed as
  `AgentConfig.memory.memory_embed_dim` — replace with a statement that
  `embed_dim` (wherever this module actually sources it — verify by reading
  `agent/factory.py`'s actual call site before finalizing) reflects the fixed
  code-level embedding dimension constant, not a config field.

## Alternatives considered

- Simply changing "384" to a new number was considered and rejected — the
  field `AgentConfig.memory.memory_embed_dim` does not exist at all; correcting
  only the number would still leave the false claim that this is a real
  `AgentConfig.memory` field.

## Implementation
### Target file
`docs/05_agent_12_03_memory-module-ref-core-and-store.md`

### Procedure
1. Re-confirm the current line number immediately before editing (verified at
   line 45 as of 2026-08-27).
2. Rewrite the sentence per Method/Details (source already confirmed:
   `factory.py:382`).
3. Run `.venv/bin/python3 tools/check_docs_consistency.py --domain agent` and
   confirm no new warning/error.

### Method
Direct text edit (Edit tool) — one sentence.

### Details
Current text (verified 2026-08-27, line 45):
```
- `embed_dim` is not in `MemoryStore` itself; it is passed by the caller `agent/factory.py` as `AgentConfig.memory.memory_embed_dim` (default: 384).
```
Replace with:
```
- `embed_dim` is not in `MemoryStore` itself; it is passed by the caller
  `agent/factory.py` (`MemoryStore(embed_dim=get_embedding_dims())` at line 382),
  sourced from `scripts/db/store_protocols.py::get_embedding_dims()` (a fixed
  code-level constant), not a config field.
```

## Compatibility considerations

- Documentation-only; no runtime behavior, config schema, or public interface
  is affected.

## Security considerations

- N/A: no security-relevant content.

## Rollback considerations

- Single-sentence text revert via `git diff`/`git checkout -- <path>`;
  independent of the other 14 target files in this Plan's pass, but should be
  cross-checked against seq 15 (`05_agent_08_03`)'s parallel correction for
  consistency of wording.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/05_agent_12_03_memory-module-ref-core-and-store.md` | Manual diff | `git diff <path>` | No fabricated `AgentConfig.memory.memory_embed_dim` field reference remains |
| `docs/05_agent_12_03_memory-module-ref-core-and-store.md` | Doc consistency check | `.venv/bin/python3 tools/check_docs_consistency.py --domain agent` | No new warning/error beyond baseline |

## Completion criteria

- No statement remains that `embed_dim` is passed as
  `AgentConfig.memory.memory_embed_dim`.

## Out of scope

- Any other content in this document.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-confirm line number | Completed | — | — | Verified at line 45 |
| 2 | Rewrite the sentence | Completed | — | — | Fabricated `AgentConfig.memory.memory_embed_dim` claim removed; actual source `factory.py:380` documented |
| 3 | Run `check_docs_consistency.py --domain agent` | Completed | — | — | Pre-existing warnings only; no new findings |

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
- **Related target files**: `docs/05_agent_12_03_memory-module-ref-core-and-store.md`
