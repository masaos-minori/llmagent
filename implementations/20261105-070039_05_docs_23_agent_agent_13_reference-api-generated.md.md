## Goal

Regenerate the generated agent reference document
`docs/23_agent/agent_13_reference-api-generated.md` with
`tools/generate_reference_table.py --type agent` so that the new public helper
`unexpected_message_keys` (created in the sibling Row 01) appears in the
`message_schema.py` function index, and confirm the regenerated document matches the
source (`--check` exits 0) (REQ-005; AC-5, AC-8).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- The document is auto-generated and guarded: content between the
  `AUTO-GENERATED` guard comments must not be hand-edited; run the generator instead
  (confirmed in Step 2; the file header says so).
- `generate_reference_table.py` scans `scripts/agent/*.py` with the AST and lists every
  public top-level function, excluding `_`-prefixed names (`--manifests` writes the
  manifest, `--check` does a two-way drift check manifest-vs-source and block-vs-manifest).
- The new public `unexpected_message_keys` is a top-level function in
  `scripts/agent/message_schema.py`, so the AST scan picks it up automatically;
  `_ALL_EPHEMERAL_KEYS` is `_`-prefixed and therefore excluded.
- The generator reads source directly (no separate manifest step required for `--type
  agent` to reflect a newly added public function).

## Design decisions

- Drive regeneration through the generator CLI (`--type agent`) rather than editing the
  guarded block by hand, so the document stays byte-consistent with the source and the
  guard-comment contract is preserved.
- Verify with `--check` after regenerating so no drift remains between the document and
  the source (AC-8).

## Alternatives considered

- Hand-inserting a line into the guarded block: rejected; the file explicitly forbids
  hand-editing between the guard comments and the generator is the source of truth.

## Implementation
### Target file
`docs/23_agent/agent_13_reference-api-generated.md`

### Procedure
1. Confirm no pre-existing drift, then regenerate, then confirm clean again.

### Method
- Baseline drift check:
  ```bash
  uv run python tools/generate_reference_table.py --type agent --check
  ```
  (exits 0 before the change; documents the starting state).
- Regenerate:
  ```bash
  uv run python tools/generate_reference_table.py --type agent
  ```
  This rewrites the guarded block from the AST scan of `scripts/agent/*.py`, adding the
  `unexpected_message_keys` row under `message_schema.py`.
- Post-regeneration drift check:
  ```bash
  uv run python tools/generate_reference_table.py --type agent --check
  ```
  Must exit 0, confirming the document now matches the source.

### Details
- After regeneration, confirm the `message_schema.py` section lists exactly four public
  functions: `validate_message`, `get_allowed_ephemeral_keys`, `is_trusted_source`, and
  the new `unexpected_message_keys`;
  `_ALL_EPHEMERAL_KEYS` must NOT appear (it is `_`-prefixed).
- Stale-reference marks: `unexpected_message_keys` is declared `(new)` in the earlier-seq
  Row 01 and resolved by the detector; nothing new is introduced in this document.

## Compatibility considerations

- Doc-only change; no code, API, or behavior changes. The document is regenerated from
  source, so it cannot drift from the actual public surface.
- This file is also targeted by `restoresummary001` (adds a public predicate) and
  `partialcount001` (removes a deleted-module row). All three are pure regenerations from
  source with no contradictory design; they only interact at implementation time when the
  source public surface changes.

## Security considerations

- None beyond ensuring the generated index reflects only the intended public surface;
  the generator excludes `_`-prefixed names, so no private helper leaks into the index.

## Rollback considerations

- Revert the document to its pre-regeneration content (git checkout) if the regeneration
  introduces unexpected rows.

## Validation plan

- `uv run python tools/generate_reference_table.py --type agent --check` exits 0 after
  regeneration (AC-8).
- Visually confirm `unexpected_message_keys` appears under `message_schema.py` and
  `_ALL_EPHEMERAL_KEYS` does not.

## Completion criteria

- `docs/23_agent/agent_13_reference-api-generated.md` lists the new public
  `unexpected_message_keys` under `message_schema.py`, the regenerated document matches
  the source (`--check` exits 0), and the guard-comment contract is preserved.

## Out of Scope

- Adding the helper (`scripts/agent/message_schema.py`, Row 01).
- The persister change (`scripts/agent/session_persister.py`, Row 02) and both test rows
  (Row 03, Row 04).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: doc-only |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
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
- **Requirement ID**: `REQ-005` (regenerate the generated reference document), `AC-5`, `AC-8`
- **Source issue**: issues/done/20261031-180407_memlogleak001_memory-persist-logs-messages.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261104-114342_memlogleak001_memory-persist-logs-messages.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-070039
- **Related target files**: docs/23_agent/agent_13_reference-api-generated.md
