# Implementation: scripts/mcp_servers/mdq/service.py (remove `self.enable_refresh`)

Source plan: `plans/20260716-131759_plan.md`

Note: a fifth distinct change targeting `service.py`, alongside the four
other `service.py` docs already created for plans 01, 02, 04, and 05 (see
`implementations/20260716-130659_service.py.md`,
`implementations/20260716-131148_mdq_service.py.md`,
`implementations/20260716-131848_mdq_service_embedding_and_search_limit_removal.py.md`,
`implementations/20260716-132317_mdq_service_summary_cache_removal.py.md`).
All five touch non-overlapping lines — apply all five.

## Goal

Remove `self.enable_refresh` — confirmed dead (read but never enforced
anywhere), following the same removal precedent already applied to
`audit_log_path` and `concurrency_limit` in this same file/config.

## Scope

**In:**
- Delete `self.enable_refresh: bool = mdq_cfg.get("enable_refresh", True)`
  (`scripts/mcp_servers/mdq/service.py:65`).

**Out:**
- `self.enable_grep` (a separate field, elsewhere in `__init__`) — this
  gate **is** enforced (`grep_docs()` raises `MdqValidationError` when
  `not self.enable_grep`) and has direct test coverage
  (`tests/test_mdq_service.py:632-644`, `TestGrepDocsConfigGate`) — do not
  touch it; it is explicitly kept as-is per the source plan's Scope.
- `self._index_lock`/`self._is_indexing` and the `index_paths()`/
  `refresh_index()` methods that use them — these implement real
  serialization and are unrelated to the dead `enable_refresh` flag; no
  change needed (the source plan adds a *test* proving this lock works,
  companion `tests/test_mdq_index_serialization.py` doc, but no
  `service.py` code change for the lock itself).

## Assumptions

1. `self.enable_refresh` is read in `service.py:65`
   (`mdq_cfg.get("enable_refresh", True)`) but never referenced anywhere
   else — verified via `rg -n "enable_refresh"
   scripts/mcp_servers/mdq/*.py` showing a single hit, the assignment
   itself. `refresh_index()` (lines 331-342) has no gate check on it at
   all — it always runs regardless of this flag's value. This is a
   genuinely dead flag, not a documented future feature, unlike
   `enable_grep`.
2. This change must land in the same commit as the companion
   `config/mdq_mcp_server.toml` doc (removes the `enable_refresh` key) —
   otherwise the config still advertises a key the code no longer reads
   (harmless but inconsistent; land together for a clean diff).

## Implementation

### Target file

`scripts/mcp_servers/mdq/service.py`

### Procedure

1. Open `scripts/mcp_servers/mdq/service.py`.
2. Locate line 65:
   ```python
   self.enable_refresh: bool = mdq_cfg.get("enable_refresh", True)
   ```
3. Delete this line in full.
4. Confirm the surrounding assignments (`self.enable_grep` immediately
   below, and whatever precedes it) remain contiguous and correctly
   indented after the deletion.

### Method

Single-line deletion — no rename, no replacement field, no enforcement
logic added (per the source plan's Design decision: removal over
enforcement, matching the `audit_log_path`/`concurrency_limit` precedent).

### Details

- Do not add a `if not self.enable_refresh: raise ...` gate inside
  `refresh_index()` — that would be new functionality (a way to disable
  the tool), never requested and explicitly not the chosen path per the
  source plan's Design section.
- Do not touch `self.enable_grep` — re-read Scope/Out above before
  editing; the two flags look similar in config but only one is wired to
  real behavior.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Field removed | `grep -n "enable_refresh" scripts/mcp_servers/mdq/service.py` | 0 matches |
| `enable_grep` intact | `grep -n "self.enable_grep" scripts/mcp_servers/mdq/service.py` | 1 match, unchanged |
| Lint | `uv run ruff check scripts/mcp_servers/mdq/service.py` | 0 errors |
| Type check | `uv run mypy scripts/mcp_servers/mdq/service.py` | no new errors |
| Grep gate unaffected | `uv run pytest tests/test_mdq_service.py -k grep -v` | still passes unchanged |
| Targeted tests | `uv run pytest tests/test_mdq_index_serialization.py -v` (once companion new-test doc lands) | all pass |
| Full MDQ suite | `uv run pytest tests/test_mdq_*.py -v` | all pass |
