## Goal

Regenerate the guarded EventBus class/function reference block in `eventbus_08_reference_api.md`
through its generator, never hand-editing the guarded block.

## Scope

- Modify only `docs/24_eventbus/eventbus_08_reference_api.md`, and only via the generator's
  output into the guarded `AUTO-GENERATED` block.

## Assumptions

- `tools/generate_reference_table.py` writes the EventBus class/function reference table into
  the guarded block of this doc; `--check` currently reports "No drift found".
- Comment/message edits in this Plan do not alter the derived class/function table, so the
  regeneration diff is expected to be empty. Regeneration enforces the "regenerate, do not
  hand-edit" contract (ADR-015 INV-01).

## Design decisions

- **Regenerate, do not hand-edit.** Run the generator with `--dry-run` first to preview, then
  without `--dry-run` to write the guarded block in place. Never edit bytes between the guard
  comments.

## Alternatives considered

- Hand-editing the table: rejected; violates ADR-015 INV-01 (guarded generated block).

## Implementation

### Target file

`docs/24_eventbus/eventbus_08_reference_api.md`

### Procedure

1. Preview the regeneration:
   `uv run python tools/generate_reference_table.py --type eventbus --dry-run`.
2. If the preview is clean (or only reflects upstream changes already committed), write in
   place:
   `uv run python tools/generate_reference_table.py --type eventbus`.
3. Confirm drift is cleared:
   `uv run python tools/generate_reference_table.py --check` — must exit 0 ("No drift found").
4. If `--check` reports drift that the generator does not resolve, stop and report
   `Blocked: generator cannot reconcile the guarded block` — do not hand-edit the block.

### Method

Run the generator; no manual edits to the doc body.

### Details

- Do not touch any text outside the guarded block.
- The expected outcome is an empty diff (the source symbols are unchanged); the step exists
  to enforce the regeneration contract, not to introduce content.

## Compatibility considerations

- Doc-only regeneration; no source or behavior change.

## Security considerations

- No security impact; documentation regeneration.

## Rollback considerations

- Revert the commit (or re-run the generator from the prior committed state).

## Validation plan

- `uv run python tools/generate_reference_table.py --check` — exits 0 ("No drift found").
- `uv run python tools/check_docs_quality.py`; `check_docs_structure.py`;
  `check_docs_content_policy.py`; `check_docs_consistency.py --domain eventbus` — no new
  issues (the `to_thread()` warning is a pre-existing false positive).

## Completion criteria

- The guarded block reflects the generator output; `--check` exits 0.

## Out of Scope

- Any edit outside the guarded block.
- Editing any other doc or source file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Regenerate guarded reference block via generator | Pending | — | — | dry-run then write; never hand-edit |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: doc-only |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A |

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
- **Requirement ID**: `REQ-004`
- **Source issue**: `issues/20261023-154326_eventbus008_documentation-comment-drift-cleanup.md`
- **Requirement requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-124800_eventbus008_documentation-comment-drift-cleanup.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261026-100803
- **Related target files**: `docs/24_eventbus/eventbus_08_reference_api.md`
