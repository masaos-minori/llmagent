## Goal

- Correct the ingestion file-lifecycle documentation so it states that every chunk file moved to `failed/` gets a `.error.json` sidecar, and that the payload-derived keys appear only when the payload is readable (`REQ-002` fallout row: the documented claim becomes inaccurate when the always-write sidecar lands).

## Scope
**Release unit**: ragrev015-core (Plan `### Release units`; owner-declared batch unit 20261110)

- The `File Lifecycle` table row for `{rag_src_dir}/chunk/{stem}-{idx:04d}.json` in `docs/21_rag/rag_02_01_ingestion_pipeline-overview.md` (current L35).

## Assumptions

- Verified at HEAD `02f3143e2`: current L35 reads "to `failed/` on failure (a `.error.json` file naming the failure reason is written for parseable payloads)". The "for parseable payloads" qualifier is accurate today because `FileRouter.write_error_metadata` returns `None` when `read_chunk_json` raises `ChunkFormatError` (`scripts/rag/ingestion/file_routing.py` L109-112), and becomes wrong after the seq-7 change.
- `docs/00_index.md` L180 already maps "Ingestion pipeline run (execute commands, file lifecycle)" to this document, so no index change is needed for this row.
- `scripts/` contains no reader of `.error.json`, so this documentation is the only description of the sidecar's shape for operators.

## Design decisions

- Reword the existing table cell in place instead of adding a new section: the lifecycle table is where an operator looks for what lands in `failed/`.
- State both facts in one sentence — always written, and payload-derived keys conditional — so the sentence stays a single table cell and does not imply the sidecar content is identical in both cases.

## Alternatives considered

- Leaving the qualifier and adding a footnote: rejected — the qualifier is the inaccurate part, and a footnote would preserve a wrong claim in the primary table.

## Implementation
### Target file
- `docs/21_rag/rag_02_01_ingestion_pipeline-overview.md`

### Procedure
- Replace the parenthetical in the `chunk/` lifecycle row's Deletion Policy cell.

### Method
- Replace `(a `.error.json` file naming the failure reason is written for parseable payloads)` with wording of this shape: `(a `.error.json` file naming the failure reason is written for every failed chunk; keys taken from the payload, such as `url` and `chunk_index`, appear only when the payload is readable)`.
- Keep the rest of the row (`Created By`, `Content`, the `registered/` destination) unchanged.

### Details
- The failure-reason values an operator can see are the `scripts/rag/exceptions.py` `IngestionFailureReason` values: `parse_failed`, `validation_failed`, `group_validation_failed`, `storage_failed`. Do not list them in this overview row; `docs/21_rag/rag_02_04_ingestion_pipeline-ingester.md` section 4.6 (seq-6 document) is where the reason values are named.
- Do not restate the command or `--force` semantics here; the section already links to `rag_05_02-execution-guide.md` (current L28).

## Compatibility considerations

- Documentation-only row. It must land in the same batch as the seq-7 implementation row, otherwise the overview describes a guarantee the code does not provide.

## Security considerations
N/A: documentation-only.

## Rollback considerations
N/A: revert the commit.

## Validation plan

- Docs gates per `routing.md`: `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_consistency.py --domain rag`, `check_docs_japanese.py` — no findings.
- Cross-check against `docs/21_rag/rag_02_04_ingestion_pipeline-ingester.md` section 4.6 wording updated by the seq-6 document; the two must not contradict each other.

## Completion criteria

- The lifecycle row no longer restricts the sidecar to parseable payloads and names the payload-derived-keys condition; all docs checkers pass (REQ-002 fallout row).

## Out of Scope

- Any other `docs/` file, including `docs/00_index.md` (mapping already correct).
- Naming the failure-reason values (seq-6 document).
- Behavior changes (seq-7 document).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the File Lifecycle row per Implementation > Procedure/Method/Details | Completed | — | 20261110-121150 |  |
| 2 | Run the documentation checkers (Validation plan) | Completed | — | 20261110-121150 | docs gates: quality/structure/content-policy/consistency(rag)/japanese all pass |

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
- **Requirement ID**: `REQ-002` (fallout row added 2026-11-10 during procedure verification: documented sidecar guarantee must match the always-write behavior)
- **Source issue**: issues/20261108-131234_ragrev015_poison-chunk-groups-retried.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-170534_ragrev015_poison-chunk-groups-retried.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261109-232810
- **Related target files**: `docs/21_rag/rag_02_01_ingestion_pipeline-overview.md`