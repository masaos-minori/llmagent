## Goal

Make the MDQ read paths report their consistency state as structured metadata, keep the display wording separate from that state, and give `get_chunk` a text-plus-metadata return (`REQ-003` machine-readable read consistency, `REQ-004` `get_chunk` metadata).

## Scope
**Release unit**: N/A: not part of a release unit

- `search_docs()` (141-144) and `grep_docs()` (409-418) fill the consistency fields in the metadata they already return.
- `get_chunk()` (146), `outline()` (205-234), and `stats()` (330-351) change from a `str` return to the text-plus-metadata pair.
- The warning text (143) and `stale_warning` (216, 231-232) stay as display output only.

## Assumptions

- `refresh_in_progress` comes from `self._is_indexing` (line 97, set at 285 and 298, cleared at 290 and 305); it is the existing source, not a new flag.
- `index_generation` is a service-level counter incremented when a refresh completes, per the plan default in the Plan's UNK-05; nothing persisted carries a generation (`index_state` holds `mtime:<path>` keys only, read at 346), so a read after a restart reports the unknown case with a nullable field rather than an invented value.
- The `get_chunk` truncation fields are the persisted columns owned by the mdqmcp004 plan and the read-time cap that was applied; this row reads them, it does not define or extend them. The per-file status and reason vocabulary owned by the mdqmcp003 plan is consumed unchanged.
- Because three read methods change return shape, the handler unpacking in `scripts/mcp_servers/mdq/mdq_server.py` must cover `outline` and `stats` as well as `get_chunk` (row 03), and the tests that treat the returned value as text must read the pair instead: rows 08, 09, and the two rows added by the Plan's 2026-11-28 fallout amendment (`tests/mcp_servers/mdq/test_mdq_stale_detection.py`, `tests/mcp_servers/mdq/test_mdq_outline_stale_helper.py`).
- `tests/mcp_servers/mdq/test_mdq_error_taxonomy.py:76,89,98` and `tests/mcp_servers/mdq/test_mdq_path_jail.py:164` call these methods only inside exception assertions, so the shape change does not affect them; they are verification dependencies, not targets.

## Design decisions

- Return the metadata as the second element of the pair, the pattern `search_docs()` and `grep_docs()` already use, rather than encoding the state into the returned text; that is what keeps `AC-5` true — a wording change cannot change the state.
- Keep `stale_warning` and the refresh warning as display text for the human-facing output, with the metadata as the authoritative state, so `docs/22_mcp/mcp_04_04_mdq.md:66` remains accurate once row 14 restates it.

## Alternatives considered

- Keep `str` returns and read the state through a separate accessor on the service: rejected, the audit detail and the dispatch result need the state per call, and an accessor would reintroduce a second source for the same fact.

## Implementation
### Target file
`scripts/mcp_servers/mdq/mdq_service.py`

### Procedure
1. Add `refresh_in_progress` and `index_generation` to the metadata each read path returns.
2. Change `get_chunk()`, `outline()`, and `stats()` to return the text plus the metadata built from the consistency state.
3. Increment the generation counter when a refresh completes (inside the existing `_is_indexing` block), and report it as nullable when no refresh has completed in this process.
4. Leave the warning strings appended to the display text as they are.

### Method

- The metadata shapes are the `TypedDict` declarations from row 01 (`SearchDocsMetadata`, `OutlineMetadata` (new), `StatsMetadata` (new), `GetChunkMetadata` (new), `GrepDocsMetadata`, `IndexPathsMetadata`); this row only fills them.
- `stats()` currently has no metadata path: `index_metadata` at 346 is display content built from raw `index_state` rows, so the new metadata carries only the consistency fields.
- `get_chunk()` reports `truncated`, `truncation_char_count`, `char_count` plus the consistency fields; the read-time cap is the effective value of `max_chars_per_chunk` after the `MdqConfig` bounds.

### Details

- The consistency state is written before the display text is assembled, so the state does not depend on whether a warning string was appended.
- `outline()`'s `stale_warning` remains a display-only field on the returned text; the state that describes is carried by `refresh_in_progress`.

## Compatibility considerations

- Test files that treat the returned value as text must be updated: rows 08, 09, 16, 17. `test_mdq_service.py:734,761,768,776,816,990,1020` and `test_mdq_get_chunk_behavior.py:70` are the concrete assertions in target rows.
- The service restart is required at deploy time (`skills/deploy/SKILL.md`), per the Plan's Affected areas row.

## Security considerations

- No new trust boundary: the metadata reports internal counters already visible through `/health`; path authorization in the read paths is unchanged.

## Rollback considerations

- N/A: revert the commit; no persisted state is written by this row.

## Validation plan

- `uv run pytest tests/mcp_servers/mdq/test_mdq_read_consistency_metadata.py tests/mcp_servers/mdq/test_mdq_index_serialization.py`
- `uv run pytest tests/mcp_servers/mdq/test_mdq_service.py tests/mcp_servers/mdq/test_mdq_stale_detection.py tests/mcp_servers/mdq/test_mdq_outline_stale_helper.py`
- `uv run ruff check scripts/mcp_servers/mdq/mdq_service.py && uv run mypy scripts/mcp_servers/mdq/mdq_service.py`
- Full sequence per `rules/toolchain.md`.

## Completion criteria

- Every read result produced during a refresh carries `refresh_in_progress` and `index_generation` (`AC-4`).
- `get_chunk` reports its truncation state in metadata, and `stats`/`outline` do so without depending on formatter wording (`AC-4`, `AC-5`).

## Out of Scope

- The metadata shapes themselves (`scripts/mcp_servers/mdq/mdq_models.py`, row 01).
- The handler and audit-detail read path (`scripts/mcp_servers/mdq/mdq_server.py`, row 03).
- Generation persistence (Plan UNK-05) and atomic generation switching (mdqmcp005).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Plan Phase 4 |
| 2 | Add or update tests per Validation plan | Pending | — | — | Assertions live in rows 08, 09, 13, 16, 17 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Row 14 states the read consistency state |

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
- **Requirement ID**: REQ-003 (read consistency state in structured metadata), REQ-004 (`get_chunk` text plus metadata)
- **Source issue**: `issues/20261119-142130_mdqmcp008_mdq-schema-scope-consistency.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-184702_mdqmcp008_mdq-schema-scope-consistency.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261128-084218
- **Related target files**: `scripts/mcp_servers/mdq/mdq_service.py`
