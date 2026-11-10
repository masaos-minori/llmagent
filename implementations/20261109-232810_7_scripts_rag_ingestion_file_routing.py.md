## Goal

- Make `FileRouter` always write a `.error.json` sidecar for every chunk file moved to `failed/`, including files whose payload cannot be parsed (`REQ-002` fallout row: always-write sidecar with a generic reason).

## Scope
**Release unit**: ragrev015-core (Plan `### Release units`; owner-declared batch unit 20261110)

- `FileRouter.route` and `FileRouter.write_error_metadata` in `scripts/rag/ingestion/file_routing.py`, plus their docstrings.

## Assumptions

- Measured at HEAD `02f3143e2` in a scratch worktree: `.error.json` has no reader in `scripts/` — `grep -rn "error\.json" scripts/` matches only the producer in `file_routing.py`. A metadata-shape change therefore breaks no code consumer; only tests and documentation describe it.
- Amended 2026-11-10 (verification): the gap is payload parsing, not a missing caller argument. `route(successful_paths, failed_paths: list[tuple[Path, str]])` (current L44-46) always receives a reason per file; the sidecar is skipped because `write_error_metadata(path, failure_reason)` returns `None` when `read_chunk_json(path)` raises `ChunkFormatError` (current L109-112), and `route()` then writes nothing for that file (current L78-89).
- This row is coupled to the seq-2 change: rejecting out-of-domain `chunk_type` at read time makes `write_error_metadata` return `None` for more payloads, so files would land in `failed/` with no explanation unless this row lands in the same batch.

## Design decisions

- Keep the caller-supplied `failure_reason` verbatim in the fallback sidecar: the reason is already known at the routing boundary (`chunk_grouping.group()` reports `parse_failed`/`validation_failed`, `ingester.py` `_route_group_failed` L395-399 forwards it), so inventing a new reason would misdescribe the failure.
- The generic part is the payload-derived metadata: when the payload is unreadable, emit the sidecar with only the envelope fields (`schema_version`, `created_by`, `failure_reason`, `timestamp`) plus `"error": "chunk payload unreadable; no metadata fields extracted"`, and omit `url`, `chunk_index`, `source_file` rather than guessing them.
- Build the fallback in `write_error_metadata` (return the fallback dict instead of `None`) rather than in `route()`, so both the routing loop (L77-89) and any direct caller of `write_error_metadata` get the same guarantee.
- Reuse existing values only: `IngestionFailureReason` (`scripts/rag/exceptions.py`) is not extended, and no new import is needed (`datetime`, `orjson` are already imported).

## Alternatives considered

- Making `route()` synthesize a reason when the tuple's reason is empty: rejected — measured call sites always pass a reason (`chunk_grouping.group()` L80-108, `_route_group_failed` L395-399, `ingester.py` partial-failure drain), so the real `None` source is the unreadable payload.
- Writing the sidecar only for parseable payloads and moving unparseable files to a separate directory: rejected — it changes the operator-visible `failed/` layout, which `docs/21_rag/rag_02_01_ingestion_pipeline-overview.md` L31-36 documents as one destination.
- Adding an `IngestionFailureReason.UNSPECIFIED` member: rejected — widens a shared enum for a case the caller already describes.

## Implementation
### Target file
- `scripts/rag/ingestion/file_routing.py`

### Procedure
- Replace the `None` return for unreadable payloads with a generic envelope sidecar, and state the always-write guarantee in both docstrings.

### Method
- Measured current shape at HEAD `02f3143e2` (`git log -1 --oneline -- scripts/rag/ingestion/file_routing.py` = `014781f94`): `route()` L44-105 (sidecar branch L77-89, unknown-reason warning L91-92, move L93-105); `write_error_metadata()` L107-133 (parse attempt L109-112, envelope L114-119, payload-derived fields L121-131).
- In `write_error_metadata`:
  - replace the `except ChunkFormatError: return None` branch (L111-12) with a fallback envelope: the same `schema_version`/`created_by`/`failure_reason`/`timestamp` keys plus `"error": "chunk payload unreadable; no metadata fields extracted"`, and return it.
  - log a warning naming `path` and the supplied `failure_reason` on that branch, with `extra={"source_type": "file", "stage_name": "ingester"}` matching the module's existing log shape.
- Update the `route()` docstring (L47) and the `write_error_metadata()` docstring (L108) to state that a sidecar is always written for a failed file and that payload-derived keys are present only when the payload is readable.

### Details
- The unknown-reason warning (`route()` L91-92, `_is_known_reason` L27-33, `_KNOWN_NON_ENUM_REASONS` L24) is unchanged: it judges the caller-supplied reason, not the sidecar shape.
- `route()`'s move loop is untouched, so a sidecar-write `OSError` (L83-89) still does not stop the file from being moved.
- The sidecar filename convention stays `{path.stem}.error.json` (L80).

## Compatibility considerations

- Two existing assertions in `tests/rag/ingestion/test_ingester.py` describe today's behavior and are re-specified by the seq-4 document in the same batch: `test_malformed_first_file_routes_group_as_parse_failed` asserts `not (failed_dir / "c0.error.json").exists()` for the unparseable file, and `test_malformed_later_file_routes_group_as_parse_failed` asserts `not (failed_dir / "c1.error.json").exists()`. Both flip to asserting a sidecar whose `failure_reason` is `parse_failed`.
- `TestIntegrityErrorPropagation` (`tests/rag/ingestion/test_ingester.py`) keeps its parseable-payload sidecar assertions unchanged.
- `docs/21_rag/rag_02_01_ingestion_pipeline-overview.md` L35 says the sidecar "is written for parseable payloads"; the seq-12 document corrects that wording in the same batch. `docs/00_index.md` L180 already maps the ingestion file-lifecycle scope to that document, so no index change is needed.

## Security considerations
N/A: writes a reason string into an operator-visible sidecar; no new input surface.

## Rollback considerations
N/A: revert the single commit.

## Validation plan

- `uv run pytest tests/rag/ingestion/test_ingester.py -q` — the sidecar-presence cases re-specified by the seq-4 document fail on HEAD and pass after this change.
- `uv run pytest tests/rag/ingestion -q` regression.
- `uv run ruff check`, `uv run mypy`, `PYTHONPATH=scripts uv run lint-imports`.

## Completion criteria

- A chunk file moved to `failed/` whose payload cannot be parsed leaves a `.error.json` whose `failure_reason` is the caller-supplied reason and which contains no payload-derived keys; parseable payloads keep their current metadata unchanged; the ingestion suites are green.

## Out of Scope

- Reading or consuming sidecars anywhere in `scripts/`.
- New `IngestionFailureReason` members.
- A dedicated `tests/rag/ingestion/test_file_routing.py`: plan target row 7 has no test row, and `FileRouter` failure routing is already exercised in `tests/rag/ingestion/test_ingester.py` (plan target row 4), where the regression assertions are re-specified.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261110-114747 | 20261110-114747 |  |
| 2 | Confirm the tests re-specified by the seq-4 document pass | Completed | — | 20261110-114823 | Tests live in `tests/rag/ingestion/test_ingester.py` (own procedure document) sidecar-presence cases in test_ingester.py green |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261110-120906 | end-of-unit gate: tests/rag/ingestion 337 passed; full suite 12133 passed; diff-cover 100%; ruff/mypy/lint-imports pass |

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
- **Requirement ID**: `REQ-002` (fallout row added 2026-11-10 during procedure verification: always write a `.error.json` sidecar, with a generic envelope when the payload is unreadable)
- **Source issue**: issues/20261108-131234_ragrev015_poison-chunk-groups-retried.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-170534_ragrev015_poison-chunk-groups-retried.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261109-232810
- **Related target files**: `scripts/rag/ingestion/file_routing.py`