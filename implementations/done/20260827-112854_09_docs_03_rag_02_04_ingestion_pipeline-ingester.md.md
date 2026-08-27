## Goal

Remove the stale `embedding_dims`-config-key claim (2 occurrences, each paired
with a stale `common.toml` docstring-reference note) in
`docs/03_rag_02_04_ingestion_pipeline-ingester.md` (REQ-004), per
`plans/20260826-151220_plan.md`.

## Scope

- In scope: both `embedding_dims`/`common.toml` line pairs (verified at lines
  153-154 and 229-230 as of 2026-08-27).
- Out of scope: any other content in this document.

## Assumptions

- `config/ingester.toml` has no `embedding_dims` key (re-verified 2026-08-27).
- The `common.toml`-does-not-exist note (lines 154, 230) is itself accurate and
  orthogonal to the `embedding_dims` config-key claim — it documents a stale
  docstring reference within the source code, not a doc-vs-code drift this Plan
  addresses; do not remove it, only correct the `embedding_dims` line it
  follows. Re-verify `common.toml`'s continued non-existence
  (`ls config/common.toml`) as a quick sanity check before editing, since if it
  now exists this separate note would itself need attention (out of this Plan's
  scope, report as `Plan Gap` if found).

## Design decisions

- Correct both `embedding_dims: Specified in config/ingester.toml (default
  384)` lines identically, since they appear to be duplicated content (possibly
  describing two related but distinct ingester code paths — verify the
  surrounding context of each occurrence before assuming they are fully
  interchangeable).

## Alternatives considered

- N/A: two narrow, parallel corrections.

## Implementation
### Target file
`docs/03_rag_02_04_ingestion_pipeline-ingester.md`

### Procedure
1. Re-confirm current line numbers for both occurrences immediately before
   editing (verified at lines 153-154 and 229-230 as of 2026-08-27).
2. Read the surrounding context of each occurrence to confirm they describe
   distinct sections (not simple duplication) before editing both identically.
3. Rewrite the `embedding_dims` line in each pair per Method/Details; leave the
   `common.toml`-does-not-exist note in each pair unchanged.
4. Confirm `config/common.toml` still does not exist
   (`ls config/common.toml` should fail) — if it now exists, do not proceed with
   this specific item's edit to the `common.toml` note without further
   investigation; report as `Needs confirmation`.
5. Run `.venv/bin/python3 tools/check_docs_consistency.py --domain rag` and
   confirm no new warning/error.

### Method
Direct text edits (Edit tool) — two `embedding_dims` line corrections; the
adjacent `common.toml` notes are read-only context, not edited.

### Details
Current text (verified 2026-08-27):
- Lines 153-154:
  ```
  - `embedding_dims`: Specified in `config/ingester.toml` (default 384).
  - docstring reference to `common.toml::embedding_dims` is outdated (`common.toml` does not exist).
  ```
- Lines 229-230 (identical):
  ```
  - `embedding_dims`: Specified in `config/ingester.toml` (default 384).
  - docstring reference to `common.toml::embedding_dims` is outdated (`common.toml` does not exist).
  ```
Replace each occurrence's first line with:
```
- Embedding dimension: fixed code-level constant returned by
  `scripts/db/store_protocols.py::get_embedding_dims()`, not a
  `config/ingester.toml` key.
```
Leave each occurrence's second line (`common.toml` docstring-staleness note)
unchanged.

## Compatibility considerations

- Documentation-only; no runtime behavior, config schema, or public interface
  is affected.

## Security considerations

- N/A: no security-relevant content.

## Rollback considerations

- Two-line-pair text revert via `git diff`/`git checkout -- <path>`;
  independent of the other 14 target files in this Plan's pass.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/03_rag_02_04_ingestion_pipeline-ingester.md` | Manual diff | `git diff <path>` | No config-key claim remains in either occurrence; `common.toml` staleness notes unchanged |
| `docs/03_rag_02_04_ingestion_pipeline-ingester.md` | Doc consistency check | `.venv/bin/python3 tools/check_docs_consistency.py --domain rag` | No new warning/error beyond baseline |

## Completion criteria

- Neither occurrence states `embedding_dims` is a `config/ingester.toml` key.

## Out of scope

- The `common.toml`-does-not-exist notes (unchanged).
- Any other content in this document.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-confirm line numbers for both occurrences | Completed | — | — | Verified at lines 153-154 and 229-230 |
| 2 | Confirm the two occurrences' surrounding context | Completed | — | — | Both describe distinct sections (not simple duplication) |
| 3 | Rewrite both `embedding_dims` lines | Completed | — | — | Both occurrences updated; no config-key claim remains |
| 4 | Confirm `config/common.toml` still does not exist | Completed | — | — | Confirmed non-existent |
| 5 | Run `check_docs_consistency.py --domain rag` | Completed | — | — | Pre-existing warnings only; no new findings |

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
- **Related target files**: `docs/03_rag_02_04_ingestion_pipeline-ingester.md`
