## Goal

Regenerate the generated API reference table so it reflects the changed public contracts of this Plan
(REQ-006, REQ-008 — the generated-reference domain is hit by the predictable fallout check).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- This file is generator output; the procedure is to run the generator, not to hand-edit the table.
- The `scripts/agent/secrets_masker.py` row currently lists only `detects_secrets`, because
  `_mask_secrets` is private; the new public helpers `redact_url` (document 01) and `redact_path`
  (document 01) appear after regeneration.
- Line 98 lists `StderrLogManager`; its entry changes because of the constructor arguments added by
  document 04.

## Design decisions

- No manual edits: the table's content is derived from source, so hand-editing would be overwritten by
  the next regeneration.

## Alternatives considered

- N/A: the generator is the only source of this document's content.

## Implementation
### Target file
`docs/23_agent/agent_13_reference-api-generated.md`
### Procedure
- Run the generator after the code rows of this Plan are implemented, then verify with the check mode.

### Method
- `uv run python tools/generate_reference_table.py` to regenerate, and
  `uv run python tools/generate_reference_table.py --check` to confirm the committed table matches the
  source.

### Details

- Expected entries after regeneration: `redact_url` (new), `redact_path` (new), and the updated
  `StderrLogManager` signature.
- Step 3b correction: the `StderrLogManager` row shows only `class StderrLogManager`, not the
  constructor signature, so document 04's added constructor arguments produce no visible change in the
  table. The regeneration instead adds `format_sqlite_error` from document 11, which the expected-entry
  list did not include.
- The generator writes the registry manifests as well as the document, so the regeneration command is
  `uv run python tools/generate_reference_table.py --manifests`; the plain form does not update the
  manifests that `--check` compares against.

## Compatibility considerations

- N/A: generated content; consumers read the table as reference only.

## Security considerations

- N/A: documentation only.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run python tools/generate_reference_table.py --check` plus the documentation gates in
  `rules/tool-gates.md` (`check_docs_structure.py`, `check_docs_content_policy.py`).

## Completion criteria

- The check mode reports no drift, and the new public helpers appear in the table.

## Out of Scope

- The code changes that produce the new public symbols (documents 01 and 04).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Regenerate the table and run the check mode | Completed | — | 20261127-040500 | regenerated with --manifests; check mode reports no drift; redact_url and redact_path present; format_sqlite_error added from document 11; Step 3b: StderrLogManager row shows only the class line so document 04 changes are not visible in the table |
| 2 | Run the documentation gates (`rules/tool-gates.md`) | Completed | 20261127-095216 | 20261127-095216 | docs gates pass (structure, content policy); awaiting end-of-batch full suite docs gates pass (structure, content policy); awaiting end-of-batch full suite; full suite: 15938 passed, 6 known baseline failures, 5 skipped; diff-cover 95%; eventbus health tests failed once under -n logical and pass serially, not baselined |

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
- **Requirement ID**: `REQ-006` (stderr log management contract) and `REQ-008` (documentation alignment)
- **Source issue**: `issues/20261119-145307_cliplc009_redaction-stderr-diagnostics.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261126-210258_cliplc009_redaction-stderr-diagnostics.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-225455
- **Related target files**: `docs/23_agent/agent_13_reference-api-generated.md`