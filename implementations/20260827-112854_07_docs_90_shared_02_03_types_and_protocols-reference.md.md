## Goal

Remove the fabricated `embedding_dims: int = 384` field from the reproduced
`DbConfig` code block in
`docs/90_shared_02_03_types_and_protocols-reference.md` (REQ-004), per
`plans/20260826-151220_plan.md`.

## Scope

- In scope: the `DbConfig` code block's `embedding_dims: int = 384` line
  (verified at line 16 as of 2026-08-27) and the adjacent validation-note
  mentioning `embedding_dims` (verified at line 19 as of 2026-08-27).
- Out of scope: every other field in the same `DbConfig` code block (still
  accurate — verify each against `scripts/db/config.py:22-32` before finalizing,
  in case other drift exists beyond this specific field).

## Assumptions

- `DbConfig` (`scripts/db/config.py:22-32`, re-verified 2026-08-27) has no
  `embedding_dims` field — this is a fabricated field reproduction, not merely a
  stale value.
- This is one of the two fabricated-field items this Plan specifically calls
  out (the other being `AgentConfig.memory.memory_embed_dim` in
  `docs/05_agent_12_03_memory-module-ref-core-and-store.md`, a separate target
  file in this same pass).

## Design decisions

- Delete the `embedding_dims: int = 384` line from the code block entirely — do
  not renumber it to `1024`, since the field does not exist on `DbConfig` at
  all.
- Remove `embedding_dims` from the `__post_init__` validation note (line 19) as
  well, matching seq 03's identical correction for the sibling doc
  (`90_shared_04_01`).

## Alternatives considered

- N/A: this is a fabricated-field removal, not a value correction — no
  alternative wording preserves a nonexistent field meaningfully.

## Implementation
### Target file
`docs/90_shared_02_03_types_and_protocols-reference.md`

### Procedure
1. Re-confirm current line numbers for the `DbConfig` code block and the
   validation note immediately before editing (verified at lines 16 and 19 as
   of 2026-08-27).
2. Read the full `DbConfig` code block (not just the excerpted lines) and
   compare every field against `scripts/db/config.py:22-32` to confirm no other
   drift exists beyond `embedding_dims`.
3. Remove the `embedding_dims: int = 384` line from the code block.
4. Remove `embedding_dims` from the `__post_init__` validation note.
5. Run `.venv/bin/python3 tools/check_docs_consistency.py --domain deployment`
   (verify correct `--domain`) and confirm no new warning/error.

### Method
Direct code-block/text edits (Edit tool) — one line deletion from a fenced code
block, one clause removal from a validation note.

### Details
Current text (verified 2026-08-27):
- Line 16 (within a `DbConfig` code block): `    embedding_dims: int = 384`
- Line 19: `- Validated in \`__post_init__\`: parent directory must exist,
  \`timeout\`/\`embedding_dims\` must be $\ge$ 1.`

Delete line 16 entirely from the code block. Change line 19 to:
```
- Validated in `__post_init__`: parent directory must exist, `timeout` must be $\ge$ 1.
```

## Compatibility considerations

- Documentation-only; no runtime behavior, schema, or public interface is
  affected.

## Security considerations

- N/A: no security-relevant content.

## Rollback considerations

- Two-line text revert via `git diff`/`git checkout -- <path>`; independent of
  the other 14 target files in this Plan's pass.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/90_shared_02_03_types_and_protocols-reference.md` | Manual diff | `git diff <path>` | No fabricated `embedding_dims` field remains in the `DbConfig` code block or validation note |
| `docs/90_shared_02_03_types_and_protocols-reference.md` | Doc consistency check | `.venv/bin/python3 tools/check_docs_consistency.py --domain deployment` (verify correct domain first) | No new warning/error beyond baseline |

## Completion criteria

- The `DbConfig` code block no longer reproduces an `embedding_dims` field.
- The validation note no longer mentions `embedding_dims`.

## Out of scope

- Every other field in the same `DbConfig` code block.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-confirm line numbers | Pending | — | — | |
| 2 | Cross-check full `DbConfig` code block against `config.py` | Pending | — | — | |
| 3 | Remove `embedding_dims` line from code block | Pending | — | — | |
| 4 | Remove `embedding_dims` from validation note | Pending | — | — | |
| 5 | Run `check_docs_consistency.py` | Pending | — | — | |

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
- **Related target files**: `docs/90_shared_02_03_types_and_protocols-reference.md`
