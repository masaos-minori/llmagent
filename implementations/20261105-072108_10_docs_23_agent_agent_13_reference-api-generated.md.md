## Goal

Regenerate `docs/23_agent/agent_13_reference-api-generated.md` so it lists the new public predicate `is_conversation_summary` (new) from `scripts/agent/history.py`, and confirm manifest/source drift is zero (REQ-007; AC-8).

## Scope
**Release unit**: N/A: not part of a release unit (Phase 5 documentation; the release unit `summary-persist-restore` covers Phases 3–4 only).

## Assumptions

- The document is a guarded, auto-generated index of public top-level classes/functions under `scripts/agent/*.py`; the text between the guard comments must be produced by the generator, never hand-edited.
- `is_conversation_summary` (new) is module-level in `scripts/agent/history.py` (Row 01), so once the source is implemented the generator includes it in the `history.py` module block.
- The generator reads the live source (or `registry/manifests/agent_api.yaml`) and writes the guarded block; `--check` performs the two-way drift check (manifest-vs-source and block-vs-manifest).

## Design decisions

- Re-run the generator with `--type agent` to re-render the guarded block from the implemented source, then run `--check` to assert the manifest and the generated block agree.
- Do not hand-edit any line between the guard comments; the generator is the single writer.

## Alternatives considered

- Hand-add the predicate to the generated index: rejected; the document forbids hand-editing between the guard comments and the drift checker would flag the divergence.

## Implementation
### Target file
`docs/23_agent/agent_13_reference-api-generated.md`

### Procedure
1. Confirm the source change is in place: `is_conversation_summary` (new) exists as a module-level function in `scripts/agent/history.py`.
2. Re-render the guarded block: `uv run python tools/generate_reference_table.py --type agent`.
3. Assert no drift: `uv run python tools/generate_reference_table.py --check` — it must exit 0.
4. If `--check` reports drift, regenerate (step 2) and re-check until clean.

### Method
```bash
uv run python tools/generate_reference_table.py --type agent
uv run python tools/generate_reference_table.py --check
```
The `history.py` module block in the rendered document now includes `is_conversation_summary` alongside `HistoryManager`, `CompressResult`, and `HistoryCompressionError`.

### Details
- `is_conversation_summary` (new) is declared in Row 01; the generator lists it because it is public and module-level.
- Stale-reference marks: none created here; the generator reads live source.

## Compatibility considerations

- The regeneration is additive: the new public predicate appears in the index; existing entries are unchanged.
- Overlap with the memory-persistence logging Plan (shares only this generated reference document): each Plan regenerates from live code; run in either order, and re-run `--check` after.

## Security considerations

- None beyond confirming the generated index matches the live source, so the reference cannot advertise a symbol that no longer exists.

## Rollback considerations

- Restore the previous generated file from git; the change is a pure regeneration.

## Validation plan

- `uv run python tools/generate_reference_table.py --check` exits 0 (AC-8).
- `is_conversation_summary` (new) appears in the `history.py` block of the rendered document.
- Docs: `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_docs_consistency.py --domain agent` — no findings.

## Completion criteria

- The regenerated document lists `is_conversation_summary` (new) under `scripts/agent/history.py`, and `uv run python tools/generate_reference_table.py --check` exits 0.

## Out of Scope

- The shared constant/predicate definition (Row 01), restore (Row 02), persistence (Row 03), the tests (Rows 04–07), and the two prose doc edits (Rows 08–09).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: documentation |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | generator --check |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | this row |

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
- **Requirement ID**: `REQ-007` (regenerate generated reference), `AC-8`
- **Source issue**: issues/done/20261031-180437_restoresummary001_session-load-drops-summary.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261104-115505_restoresummary001_session-load-drops-summary.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-072108
- **Related target files**: docs/23_agent/agent_13_reference-api-generated.md
