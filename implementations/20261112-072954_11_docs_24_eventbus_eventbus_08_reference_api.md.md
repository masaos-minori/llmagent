## Goal

Regenerate the guarded AUTO-GENERATED reference block in `docs/24_eventbus/eventbus_08_reference_api.md` so it includes the new `count_failed_outbox(db)` function from `scripts/eventbus/dlq_repo.py` (sibling procedure, seq 01), and confirm no drift (`REQ-007` / `AC-7`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `scripts/eventbus/dlq_repo.py` gains `count_failed_outbox(db) -> int` (or `int | None`), documented in seq 01.
- `eventbus_08` is a generated document: its body is produced by `tools/generate_reference_table.py`, and two `AUTO-GENERATED` markers delimit the regenerable block (line ~108 lists `dlq_repo.py`'s `get_outbox_state`).
- The generator reads the live source, so once seq 01's function exists, regenerating includes it automatically.
- The `--check` mode fails (non-zero exit) if the committed block drifts from the current source.

## Design decisions
- Do not hand-edit the generated block. Run the generator to rewrite it, then run `--check` to confirm zero drift.
- If the generator does not emit the new function (e.g. it is excluded by a signature filter), add a targeted note in the `dlq_repo.py` section of the block — but prefer the tool's output.

## Alternatives considered
- Hand-inserting a row for `count_failed_outbox` into the generated table: rejected — the block is machine-generated; a manual edit would be overwritten on the next regeneration and could drift.

## Implementation
### Target file
`docs/24_eventbus/eventbus_08_reference_api.md`

### Procedure
1. Ensure seq 01's `count_failed_outbox` is implemented in `scripts/eventbus/dlq_repo.py` (it is, before this step runs).
2. Regenerate: `uv run python tools/generate_reference_table.py --type eventbus`.
3. Verify: `uv run python tools/generate_reference_table.py --check` — must exit 0 (no drift).
4. Confirm the regenerated `dlq_repo.py` section now lists `count_failed_outbox` with its signature and a description.
5. Do not hand-edit any other line of the generated block.

### Method
```bash
uv run python tools/generate_reference_table.py --type eventbus
uv run python tools/generate_reference_table.py --check
```
If `--check` still reports drift after regeneration, inspect whether `count_failed_outbox` matches the generator's inclusion rules (public module-level function with a docstring); if it is correctly includable and still missing, report the tool behavior rather than hand-editing.

### Details
- The generator scans `scripts/eventbus/*.py` public symbols and writes the table rows between the `AUTO-GENERATED` markers; adding a public function to `dlq_repo.py` is enough for it to appear after regeneration.
- Keep the description terse and parallel to the existing `dlq_repo.py` rows (e.g. "Return the number of terminal-failed `dlq_outbox` rows, or 0/None on query failure.").
- The rest of `eventbus_08` is unchanged; only the regenerated block is rewritten.

## Compatibility considerations
- Generated artifact. No other Plan targets `eventbus_08`; `generate_reference_table.py --check` must pass.

## Security considerations
- None: API reference documentation only.

## Rollback considerations
- N/A: revert the commit; the regenerated block is deterministic from source.

## Validation plan
- `uv run python tools/generate_reference_table.py --check` — exit 0, no drift.
- `uv run python tools/check_docs_consistency.py --domain eventbus` — pass.
- `uv run python tools/check_docs_content_policy.py --strict`, `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_japanese.py` — pass.

## Completion criteria
- `eventbus_08`'s generated `dlq_repo.py` section lists `count_failed_outbox` with its signature.
- `generate_reference_table.py --check` passes with no drift.

## Out of Scope
- Implementing `count_failed_outbox` — sibling procedure (`scripts/eventbus/dlq_repo.py`, seq 01).
- Any non-generated edit to `eventbus_08`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: `REQ-007` — regenerate `eventbus_08` to include the new `dlq_repo.py` function; `generate_reference_table.py --check` passes
- **Source issue**: issues/20261109-113152_adrrev014_eventbus-spec-gaps.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-103238_adrrev014_eventbus-spec-gaps.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-072954
- **Related target files**: `docs/24_eventbus/eventbus_08_reference_api.md`
