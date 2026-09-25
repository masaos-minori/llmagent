# Merge eventbus docs into new eventbus folder

## Priority
Medium

## Summary
`git mv` the 8 flat `docs/06_eventbus_*.md` files and the entire existing
`docs/eventbus/` directory (9 files) into one new `docs/24_eventbus/` subfolder. No
filename or content change beyond required reference fixups and baseline updates.

## Background
Same `docs/` reorganization effort as `docsreorg05`; see that issue's Background for
full context. This is the one area where two independently-numbered file sets merge
into a single folder — see Problem for the resulting numbering overlap, which this
issue explicitly does not resolve (no renaming).

## Problem
Two independent sets of eventbus docs currently exist:
- 8 flat files directly under `docs/`: `docs/06_eventbus_00_document-guide.md`,
  `docs/06_eventbus_01_system-overview.md`, `docs/06_eventbus_02_operations.md`,
  `docs/06_eventbus_03_persistence_schema_and_replay.md`,
  `docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md`,
  `docs/06_eventbus_05_07_validation-status.md`,
  `docs/06_eventbus_05_configuration-and-operations.md`,
  `docs/06_eventbus_06_reference-api.md`.
- 9 files already under `docs/eventbus/`: `01_dlq_operations.md`,
  `02_dlq_requeue_api.md`, `03_replay_operations.md`, `08_publish_durability.md`,
  `ack-nack-endpoints.md`, `dlq-endpoint.md`, `health-endpoint.md`, `index.md`,
  `replay-endpoint.md`.

Both sets use their own independent leading-number scheme (e.g. `06_eventbus_01_...`
and `eventbus/01_dlq_operations.md` both start with "01" but refer to unrelated
documents). No filename collision exists (confirmed: stripping each set's own prefix
still yields globally-unique names), but once merged into one folder, a reader sees two
numbering series side by side. This issue moves both sets into one folder as-is;
resolving the numbering overlap for readability is an explicit non-goal (see Out of
Scope) and a separate, later decision if pursued at all.

## Reason for Change
Same rationale as `docsreorg05`: both sets cover the eventbus domain and belong in one
area folder, even though a full unification of their numbering is a separate concern.

## Implementation Intent
Use `git mv` only — do not rename any file, and do not renumber either series. Move
the 8 flat files and the entire `docs/eventbus/` directory's 9 files into
`docs/24_eventbus/` (flattening `docs/eventbus/` — it does not become a nested
sub-subfolder inside `docs/24_eventbus/`).

## Target Files or Areas
- `docs/06_eventbus_00_document-guide.md` → `docs/24_eventbus/06_eventbus_00_document-guide.md`
- `docs/06_eventbus_01_system-overview.md` → `docs/24_eventbus/06_eventbus_01_system-overview.md`
- `docs/06_eventbus_02_operations.md` → `docs/24_eventbus/06_eventbus_02_operations.md`
- `docs/06_eventbus_03_persistence_schema_and_replay.md` → `docs/24_eventbus/06_eventbus_03_persistence_schema_and_replay.md`
- `docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md` → `docs/24_eventbus/06_eventbus_04_dlq_offsets_and_delivery_semantics.md`
- `docs/06_eventbus_05_07_validation-status.md` → `docs/24_eventbus/06_eventbus_05_07_validation-status.md`
- `docs/06_eventbus_05_configuration-and-operations.md` → `docs/24_eventbus/06_eventbus_05_configuration-and-operations.md`
- `docs/06_eventbus_06_reference-api.md` → `docs/24_eventbus/06_eventbus_06_reference-api.md`
- `docs/eventbus/01_dlq_operations.md` → `docs/24_eventbus/01_dlq_operations.md`
- `docs/eventbus/02_dlq_requeue_api.md` → `docs/24_eventbus/02_dlq_requeue_api.md`
- `docs/eventbus/03_replay_operations.md` → `docs/24_eventbus/03_replay_operations.md`
- `docs/eventbus/08_publish_durability.md` → `docs/24_eventbus/08_publish_durability.md`
- `docs/eventbus/ack-nack-endpoints.md` → `docs/24_eventbus/ack-nack-endpoints.md`
- `docs/eventbus/dlq-endpoint.md` → `docs/24_eventbus/dlq-endpoint.md`
- `docs/eventbus/health-endpoint.md` → `docs/24_eventbus/health-endpoint.md`
- `docs/eventbus/index.md` → `docs/24_eventbus/index.md`
- `docs/eventbus/replay-endpoint.md` → `docs/24_eventbus/replay-endpoint.md`
- `tests/tools/test_check_docs_quality.py` (`EXPECTED_WITHIN_FILE_PAIRS` — 34 entries
  keyed to `06_eventbus_*.md` bare filenames, plus 9 entries already keyed to
  `eventbus/*.md`)

## Required Changes
- `git mv` each of the 8 flat `06_eventbus_*.md` files into `docs/24_eventbus/`.
- `git mv` each of the 9 files currently under `docs/eventbus/` into
  `docs/24_eventbus/` directly (not into a nested `docs/24_eventbus/eventbus/`), which
  retires the `docs/eventbus/` directory entirely.
- Update `tests/tools/test_check_docs_quality.py`'s `EXPECTED_WITHIN_FILE_PAIRS`:
  change all 34 keys currently prefixed with a bare `06_eventbus_*.md` filename to
  `24_eventbus/06_eventbus_*.md`, and change all 9 keys currently prefixed with
  `eventbus/*.md` to `24_eventbus/*.md` (dropping the old `eventbus/` segment, adding
  the new `24_eventbus/` segment).
- Confirm `docsreorg01` and `docsreorg02` have landed before merging this move.

## Constraints
- `git mv` only — no filename change, no renumbering of either series, no content
  rewriting beyond what `docsreorg04` already covers.
- Do not create a nested `docs/24_eventbus/eventbus/` subfolder — both sets land
  directly in `docs/24_eventbus/`.

## Acceptance Criteria
- `git log --follow` on each of the 17 moved files shows continuous history through
  the move.
- `docs/eventbus/` no longer exists as a tracked directory after the move.
- `uv run python tools/check_docs_structure.py "docs/**/*.md" --schema schemas/doc_front_matter.json`
  reports zero new findings introduced by this move.
- `uv run python -m tools.check_docs_quality` passes (or reports only pre-existing,
  unrelated findings).
- `uv run pytest tests/tools/test_check_docs_quality.py -q` passes with the updated
  `EXPECTED_WITHIN_FILE_PAIRS` (43 keys updated: 34 + 9).

## Testing Expectations
- `uv run python tools/check_docs_structure.py "docs/**/*.md" --schema schemas/doc_front_matter.json`
- `uv run python -m tools.check_docs_quality`
- `uv run pytest tests/tools/ -q`

## Documentation Impact
This issue is itself the documentation-location change for the eventbus area. If a
later, separate decision is made to unify the two numbering series, that is a distinct
follow-up issue, not part of this one.

## Out of Scope
- Renumbering either the `06_eventbus_*` series or the `eventbus/*` series to remove the
  numbering overlap noted in Problem.
- Any filename change or prefix removal.
- Any content edit beyond what `docsreorg04` already covers.

## Dependencies
- Depends on: `docsreorg01`, `docsreorg02`.
- Coordinate with: `docsreorg04` (canonical reference updates).

## Unresolved Questions
- Whether the two numbering series should eventually be unified for readability is
  explicitly deferred, not resolved by this issue — flagged here so it is not
  forgotten, not because it blocks this move.

## AI Implementation Instruction
Move the 8 flat `06_eventbus_*.md` files and all 9 files under `docs/eventbus/` into
`docs/24_eventbus/` (flat, no nested subfolder), using `git mv`, with no filename or
numbering changes. Update the 43 `EXPECTED_WITHIN_FILE_PAIRS` keys as described. If
`docsreorg01`/`docsreorg02` have not landed yet, stop and report `Blocked`.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260923-141307
- **Related target files**: docs/06_eventbus_00_document-guide.md, docs/06_eventbus_01_system-overview.md, docs/06_eventbus_02_operations.md, docs/06_eventbus_03_persistence_schema_and_replay.md, docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md, docs/06_eventbus_05_07_validation-status.md, docs/06_eventbus_05_configuration-and-operations.md, docs/06_eventbus_06_reference-api.md, docs/eventbus/01_dlq_operations.md, docs/eventbus/02_dlq_requeue_api.md, docs/eventbus/03_replay_operations.md, docs/eventbus/08_publish_durability.md, docs/eventbus/ack-nack-endpoints.md, docs/eventbus/dlq-endpoint.md, docs/eventbus/health-endpoint.md, docs/eventbus/index.md, docs/eventbus/replay-endpoint.md, tests/tools/test_check_docs_quality.py
