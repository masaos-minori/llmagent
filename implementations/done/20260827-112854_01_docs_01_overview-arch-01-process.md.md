## Goal

Replace the literal chat-LLM/embed-LLM model names in
`docs/01_overview-arch-01-process.md`'s service/port/model table with a
cross-reference to `docs/02_deployment.md` §1.4 (REQ-001, REQ-002), per
`plans/20260826-151220_plan.md`.

## Scope

- In scope: the `agent-llm` row (line 74) and `embed-llm` row (line 75) of the
  service/port/model table in this one file.
- Out of scope: any other row of the table; `docs/02_deployment.md` itself (not
  modified — it is already the canonical source, per prior Plan
  `plans/done/20260819-174858_plan.md`); resolving which literal `.gguf` filename
  is actually correct (this Plan's UNK-01, out of scope — the cross-reference fix
  does not require that answer).

## Assumptions

- `docs/02_deployment.md` §1.4 remains the project's canonical model-reference
  table (established by `plans/done/20260819-174858_plan.md`) — re-verified
  2026-08-27, the table still exists at that document with a "Canonical source"
  callout.
- **Correction (plan-to-implementation-procedure adversarial verification,
  2026-08-27)**: the embed-LLM model NAME itself (`multilingual-e5-small` in
  `02_deployment.md` vs. `multilingual-E5-small` here) does not actually conflict
  — only capitalization differs. REQ-002's cross-reference of the model name is a
  preventive consistency measure, not a correction of an existing name conflict;
  the genuine, confirmed defect for this row is the "384D" dimension claim. The
  chat-LLM row (REQ-001) has the real three-way name conflict: this file says
  `Qwen3.6-Instruct-Q4_K_M`, while `02_deployment.md` §1.4 itself lists two
  different names for the LLM role (`gemma-4-e4b-it`,
  `Qwopus3.6-35B-A3B-v1`) — none of the three match.

## Design decisions

- Mirror the cross-reference pattern already established and implemented for
  `docs/01_overview-files-01-build.md` and
  `docs/03_rag_05_1-configuration-reference.md` (per this Plan's Implementation
  intent) — read one of those two files' actual cross-reference wording before
  finalizing this edit, to match established phrasing exactly rather than
  inventing new wording.
- Replace the Model column value with a link/reference to
  `docs/02_deployment.md#14-llm--how-to-get-models` (or the section's current
  anchor — verify the exact anchor slug by reading `02_deployment.md`'s rendered
  heading ID before finalizing).
- For the embed-LLM row, also remove the standalone "384D Vector conversion"
  dimension claim per REQ-004's sourcing rule (point to
  `scripts/db/store_protocols.py::get_embedding_dims()` instead of restating a
  number) — do not simply drop the dimension mention with no replacement context.

## Alternatives considered

- Correcting the chat-LLM name to one specific literal value (rather than
  cross-referencing) was considered and rejected — this Plan's own Scope/Design
  explicitly defers resolving which literal filename is correct (UNK-01) to a
  future operator/maintainer answer; a cross-reference avoids asserting an
  unconfirmed literal value here.

## Implementation
### Target file
`docs/01_overview-arch-01-process.md`

### Procedure
1. Re-confirm current line numbers for the `agent-llm`/`embed-llm` rows
   immediately before editing (verified at lines 74-75 as of 2026-08-27; per this
   Plan's own Phase 1 preparation step, re-confirm they have not shifted).
2. Read `docs/01_overview-files-01-build.md` or
   `docs/03_rag_05_1-configuration-reference.md`'s existing cross-reference
   wording (established by the prior plan) to match phrasing conventions.
3. Replace the `agent-llm` row's Model column value with the cross-reference
   (REQ-001).
4. Replace the `embed-llm` row's Model/dimension column value with the same
   cross-reference pattern, removing the "384D" claim (REQ-002).
5. Run `.venv/bin/python3 tools/check_docs_consistency.py --domain overview`
   (per this Plan's documented `uv run` fallback) and confirm no new
   warning/error beyond the recorded baseline (2 pre-existing broken-link
   errors, unrelated to this Plan).

### Method
Direct text edits (Edit tool) — two table cell replacements.

### Details
Current table rows (verified 2026-08-27, lines 74-75):
```
| `agent-llm` | 8080 | Qwen3.6-Instruct-Q4_K_M | Chat/Code Generation LLM (Dual use: MQE & Re-ranking) |
| `embed-llm` | 8081 | multilingual-E5-small | Text → 384D Vector conversion |
```
Replace with (adjust wording to match the established cross-reference pattern
found in step 2 above; this is a draft shape):
```
| `agent-llm` | 8080 | See [docs/02_deployment.md §1.4](./02_deployment.md#14-llm--how-to-get-models) | Chat/Code Generation LLM (Dual use: MQE & Re-ranking) |
| `embed-llm` | 8081 | See [docs/02_deployment.md §1.4](./02_deployment.md#14-llm--how-to-get-models) | Text → Vector conversion (dimension: `scripts/db/store_protocols.py::get_embedding_dims()`) |
```
Verify the exact Markdown link anchor slug by inspecting how
`docs/01_overview-files-01-build.md`/`docs/03_rag_05_1-configuration-reference.md`
already link to this same section, rather than guessing the anchor independently.

## Compatibility considerations

- Documentation-only; no runtime behavior, config schema, or public interface is
  affected.

## Security considerations

- N/A: no security-relevant content.

## Rollback considerations

- Two-cell text revert via `git diff`/`git checkout -- <path>`; independent of
  the other 14 target files in this Plan's pass.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/01_overview-arch-01-process.md` | Manual diff | `git diff docs/01_overview-arch-01-process.md` | `agent-llm`/`embed-llm` rows cross-reference `docs/02_deployment.md` §1.4; no literal model name or "384D" claim restated |
| `docs/01_overview-arch-01-process.md` | Doc consistency check | `.venv/bin/python3 tools/check_docs_consistency.py --domain overview` (or `uv run` equivalent if network access is available) | No new warning/error beyond the 2 pre-existing broken-link errors |

## Completion criteria

- The `agent-llm`/`embed-llm` rows no longer state a literal model name/dimension
  that conflicts with, or duplicates and risks drifting from,
  `docs/02_deployment.md` §1.4.

## Out of scope

- Any other row of this table.
- `docs/02_deployment.md` itself.
- Resolving UNK-01 (which literal filename is actually correct).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-confirm line numbers | Completed | — | — | Verified at lines 74-75 |
| 2 | Read established cross-reference wording from precedent files | Completed | — | — | Pattern matched: `See [docs/02_deployment.md section 1.4](./02_deployment.md#14-llm--How to get models) for canonical model names` |
| 3 | Replace `agent-llm` row's Model value | Completed | — | — | Literal model name replaced with cross-reference |
| 4 | Replace `embed-llm` row's Model/dimension value | Completed | — | — | Literal model name + "384D" claim replaced; dimension now references fixed constant |
| 5 | Run `check_docs_consistency.py --domain overview` | Completed | — | — | Pre-existing warnings only; no new findings |

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
- **Requirement ID**: REQ-001, REQ-002
- **Source issue**: `issues/20260821_10_issue.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260826-151220_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260827-112854
- **Related target files**: `docs/01_overview-arch-01-process.md`
