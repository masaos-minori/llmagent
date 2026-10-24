## Goal

Regenerate the guarded AUTO-GENERATED agent class/function reference block in
`docs/23_agent/agent_13_reference-api-generated.md` after the `mask_args` docstring change, so the
generated index matches the source docstrings (`REQ-005`, `AC-7`).

## Scope

- `docs/23_agent/agent_13_reference-api-generated.md`: the block delimited by the AUTO-GENERATED
  markers at `:30` and `:196`. The `mask_args` row is at `:184`.
- Generator output only. No hand edits inside the block, and no change to the document's front matter,
  `## Purpose`, or any section outside the block.

## Assumptions

- `tools/generate_reference_table.py` reads only `scripts/agent/*.py` non-recursively, skips
  `_`-prefixed files and symbols, and takes each Summary from the first docstring line. Therefore
  `_mask_value` (new) never appears in this table, and only the `mask_args` first line changes the
  output.
- The only row affected by this Plan cycle is `mask_args`; the measured delta is +11 bytes.
- The accepted size ceiling for this document is 24972 B in `SIZE_EXCEPTIONS`
  (`tools/check_docs_structure.py:114`), recorded when `BLK-001` was cleared.

### Procedure-local findings

- The Plan cites the AUTO-GENERATED markers at `agent_13:31` and `:195` and the `mask_args` row at
  `:180`. Measured: markers at `:30` and `:196`, row at `:184`. Recorded in the Plan's corrections
  subsection.
- `REQ-005`'s "stays under the size limit" cannot hold without the accepted exception; the constraint
  and its measured basis are recorded in `plans/20261023-072425_plan.md` (`BLK-001`).
- `uv run python tools/check_docs_structure.py '23_agent/agent_13_*.md'` (the form the Plan's Validation
  plan used) exits 0 while checking nothing; use the `docs/`-prefixed form
  (`issues/20261024-124138_docs010_check_docs_structure-glob-matching-no-files-passes-silently.md`).

## Design decisions

- Regenerate rather than hand-edit the row, because `tools/generate_reference_table.py --check` gates CI:
  INV-01 in `docs/10_adr/adr_02_07_015_docs-reference-document-class-disposition.md:109` states that a
  migrated Reference-class document has its guarded-block content produced only by the generator, and
  `routing.md:108` routes any change under `scripts/agent/` to that generator.
- Order this row after `implementations/20261024-124138_01_scripts_agent_tool_result_formatter.py.md`:
  the regenerated content depends on the final docstring text, so running this row first would produce
  a block that immediately goes stale.
- Keep the `mask_args` first line at the measured 77-character wording. The accepted ceiling equals the
  post-change size exactly (24972 B), so a longer first line pushes the file past its ceiling and
  requires re-measuring and re-accepting the exception.

## Alternatives considered

- Editing the `mask_args` Summary cell by hand: rejected. It desyncs the block from the generator and
  fails `--check`.
- Shortening the docstring so the file stays under `MAX_SIZE` without an exception: reconsidered after
  the fact. The exception already exists and was measured against the accepted wording; shortening the
  docstring now would trade a documented boundary statement for 396 bytes of headroom it does not need.
- Splitting the generated table into two documents to stay under `MAX_SIZE`: rejected. It changes the
  reference-doc layout for a 396 B margin problem that the accepted exception already covers.

## Implementation

### Target file

`docs/23_agent/agent_13_reference-api-generated.md` — the block between the AUTO-GENERATED markers at
`:30` and `:196`.

### Procedure

1. Land `implementations/20261024-124138_01_scripts_agent_tool_result_formatter.py.md` first.
2. Run `uv run python tools/generate_reference_table.py --type agent`.
3. Confirm the `mask_args` row (`:184`) now carries the new first line and that no other row changed.
4. Run `uv run python tools/generate_reference_table.py --type agent --check` and confirm exit 0.
5. Run `uv run python tools/check_docs_structure.py "docs/23_agent/agent_13_*.md"` and confirm exit 0
   against the accepted ceiling.

### Method

- The generator rewrites the guarded block in place; the row content is the docstring first line, so
  the change is text propagation, not authoring.
- Compare only the target row when diffing: the generator's File column reflects the tree it scanned, so
  a whole-table diff is noisy if the run is ever done from a probe tree.

### Details

- Expected measured size after regeneration: 24972 B, up from 24961 B at HEAD `6fcbb7e0c`.
- Expected drift surface: exactly one row (`mask_args`). Any other row changing in the same diff means
  another source docstring moved and must be explained before committing.

## Compatibility considerations

- `--check` is a CI gate; a committed source docstring and a stale block fail the pipeline.
- The document's front matter `related:` entry (`agent_12_reference-api.md`) is unchanged, so
  `tools/check_docs_structure.py`'s Related-coverage rule is not affected.
- The size exception lives in `tools/check_docs_structure.py:114`, a file no row of this Plan targets.
  If this document's size changes again for any other reason, that entry must be re-measured and
  re-accepted rather than exceeded.

## Security considerations

- N/A: a generated index of public symbols and docstring summaries. It exposes no secret, and masking
  behavior is documented in
  `implementations/20261024-124138_05_docs_23_agent_agent_08_03_configuration-tools-memory.md.md`.

## Rollback considerations

- Reverting the source docstring requires re-running the generator in the same commit; a reverted source
  with a regenerated-out-of-date block breaks `--check`.
- The `SIZE_EXCEPTIONS` entry describes the post-change accepted size. A rollback that shrinks the file
  leaves the entry larger than necessary but does not fail any check; the comment at
  `tools/check_docs_structure.py:108-114` should be updated to match the new measured size.

## Validation plan

- `uv run python tools/generate_reference_table.py --type agent --check` — exits 0 (`AC-7`).
- `uv run python tools/check_docs_structure.py "docs/23_agent/agent_13_*.md"` — exits 0 through the
  accepted 24972 B ceiling.
- `uv run python tools/check_docs_structure.py "docs/**/*.md"` — the whole-docs form used by CI
  (`.github/workflows/governance-docs-consistency.yml:89`), exits 0.
- `git diff --stat docs/23_agent/agent_13_reference-api-generated.md` — the diff touches the
  `mask_args` row only.

## Completion criteria

- `AC-7`: `--check` exits 0 and the `agent_13` `mask_args` row matches the new docstring first line.
- The regenerated file measures 24972 B and passes `tools/check_docs_structure.py` with the accepted
  exception; no new exception is added by this row.
- `AC-8`: the full `rules/toolchain.md` sequence passes with no new failure.

## Out of Scope

- Editing any row of the generated table by hand.
- Changing `MAX_SIZE`, `SIZE_EXCEPTIONS`, or `tools/check_docs_structure.py` — the ceiling entry for this
  cycle already exists at `:114`.
- Documenting the boundary rule, owned by
  `implementations/20261024-124138_05_docs_23_agent_agent_08_03_configuration-tools-memory.md.md`.
- The `args_preview` field, which is absent from this document and undocumented repo-wide
  (`issues/20261024-124138_tool005-args-preview-is-written-to-the-audit-log-unbounded.md`).


## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Regenerate the guarded block after `_01` lands | Pending | — | — | Generator only |
| 2 | Confirm `--check` exits 0 | Pending | — | — | `AC-7` |
| 3 | Confirm the measured size is 24972 B and the size checker passes | Pending | — | — | Accepted ceiling at `tools/check_docs_structure.py:114` |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | `BLK-001`: regenerating the block takes the file to 24972 B against a 24576 B `MAX_SIZE`, and no frozen row authorizes changing the checker | Yes — accepted per-file ceiling 24972 B recorded in `SIZE_EXCEPTIONS` (`tools/check_docs_structure.py:114`) | 2026-10-24 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | N/A: no work item was created by this row |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-005`
- **Source issue**: `issues/20261021-093421_tool005-masked-args-not-applied-to-previews-or-nesting.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261023-072425_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261024-124138
- **Related target files**: `docs/23_agent/agent_13_reference-api-generated.md`
