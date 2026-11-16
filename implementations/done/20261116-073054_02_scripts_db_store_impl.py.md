## Goal
- In `scripts/db/store_impl.py`: reject negative `older_than_days` in `delete_memories_before`/`collect_prunable_ids` (REQ-005) and rewrite the three store cutoff queries to the stored `T/Z` format (REQ-004), with `tests/db/test_db_store_impl.py` as companion covering the AC-1/AC-2 boundaries.

## Scope
**Release unit**: retention-input-validation (Phases 1-3 of the plan; lands with `20261116-073054_01`, `_03`..`_05`)

- In scope: `scripts/db/store_impl.py` (`:177-214` region) guards + cutoffs; companion `tests/db/test_db_store_impl.py` negative/boundary tests.
- Out of scope: `MemoryDeleteResult.deleted_ids` (Plan 006, landed procedure `20261116-072110_03` — 007 edits no region it lands); maintenance-side guards/cutoffs (procedure `20261116-073054_01`); config tests (companion in `_03`); docs update (plan Phase 3).

## Assumptions
- Verification finding (2026-11-16, re-confirmed against source at HEAD `d0500d87c`): `delete_memories_before` (`:177-207`) has its fast-path SELECT cutoff at `:182` and the `DELETE ... RETURNING` cutoff at `:192`; `collect_prunable_ids` (`:209-216`) cutoff SELECT at `:213`; all three compare `updated_at < datetime('now', ?)`; no guard on `older_than_days` anywhere in `:177-216`. (Line anchors updated 2026-11-16 from the generation-time positions.)
- Gated by Plan 006 (phase all, now `plans/done/`): the landed `delete_memories_before` returns `deleted_ids=tuple(...)` (procedure `20261116-072110_03`, `store_impl.py:206`); the guards land at the top of both methods, outside the landed `begin_immediate` block (`:189`), and must preserve the `deleted_ids` construction. Marker text kept; Plan 006 code is already landed at HEAD `d0500d87c` (see Execution Status note).
- `memory_prune` already validates `--days >= 1` (`scripts/agent/commands/memory_data_ops.py:134-155`, `days < 1` check at `:149-150`) and its dry-run `collect_prunable_ids` usage (`:374`) only passes validated values — the new guard protects direct/API callers without breaking the consumer (plan Reference Files).
- Companion eligibility for `tests/db/test_db_store_impl.py`: plan table row 6 under `tests/`, named in exactly one other row's Related Tests (this row), fully prescribed tests, same real-DB harness as the code row — no design decision of its own (SKILL.md companion conditions 1-4).

## Design decisions
- Guard at both store entry points (`collect_prunable_ids` and `delete_memories_before`) so dry-run and delete paths fail identically (REQ-005; AC-1).
- `older_than_days == 0` stays meaningful (cutoff = now — today's documented prune semantics); only negatives raise (plan Design, semantics table: no "disabled" concept for memories).

## Alternatives considered
- Guarding only `delete_memories_before`: rejected — a negative dry-run would return a bogus count instead of failing closed.
- Silent clamp of negatives: rejected — the maintainer decision is reject (AC-1).

## Implementation
### Target file
`scripts/db/store_impl.py`

### Procedure
1. At the top of `delete_memories_before` (`:177`) and `collect_prunable_ids` (`:209`): `if older_than_days < 0: raise ValueError("older_than_days must be >= 0, got <value>")` — before any SELECT/`begin_immediate` (`:189`) (REQ-005; plan Phase 2, after re-reading Plan 006's landed flow).
2. Rewrite the three cutoff comparisons `:182`, `:192`, `:213` from `datetime('now', ?)` to `strftime('%Y-%m-%dT%H:%M:%SZ', 'now', ?)`, keeping the `f"-{older_than_days} days"` parameter unchanged; `0` yields cutoff = now (REQ-004).
3. Docstrings of both methods: state the `>= 0` contract and the `0` = cutoff-now meaning (REQ-005 documentation).

### Companion test files
- `tests/db/test_db_store_impl.py`
  - Procedure: add `delete_memories_before(-1)` and `collect_prunable_ids(-1)` → `ValueError` tests; add a `days=0` boundary test seeding one memory stamped 5 s older and one 5 s newer than `utcnow` in the stored `T/Z` literal format → older deleted, newer kept; keep every existing `days=30/7` test (`:401-627`) unchanged.
  - Validation: `uv run pytest tests/db/test_db_store_impl.py -v` → AC-1/AC-2 asserted; existing delete tests stay green (plan Tests regression watch).

### Method
- Direct edits inside the existing class; no new imports; radon baseline `delete_memories_before` B(7) — the guard adds ≤ 1 branch, extract the guard message builder if the top exceeds B(7) (plan Validation plan).

### Details
- The `NULL` silent no-op the Issue observed (`f"--5 days"` → NULL comparison) disappears with the guard before any SQL runs (plan row evidence: confirmed live Step 2).
- Sequence context: Plan 008 later extends store retention paths (artifact retention); it edits no region this document lands.

## Compatibility considerations
- `memory_prune` consumer unaffected (`--days >= 1` validated upstream; grep this cycle found no other in-repo caller passing unvalidated ints — plan Risks).
- Cutoff fix deletes up to one day more for `T/Z`-stamped rows (same UNK-01 operator confirmation as procedure `_01`).

## Security considerations
- Fail-closed guard replaces a silent no-op; bandit baseline 45 low / 0 medium / 0 high unchanged (queries stay parameterized).

## Rollback considerations
- `git checkout` revert of the unit commit; part of release unit retention-input-validation — revert together with `_01`, `_03`..`_05` (its companion tests are part of this document).

## Validation plan
- `uv run pytest tests/db/test_db_store_impl.py -v` → companion tests assert AC-1/AC-2; pre-existing tests (`:401-627`) green unchanged.
- `uv run pytest tests/ -n auto` → no regressions (memory_prune command, maintenance prune).
- `uv run radon cc scripts/db/store_impl.py -s` → top ≤ B(7); `uv run ruff check scripts/db/store_impl.py`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools` (CI form), `uv run lint-imports` → 6 contracts kept.

## Completion criteria
- `delete_memories_before(-1)` and `collect_prunable_ids(-1)` raise `ValueError` before touching SQL; `delete_memories_before(0)` deletes exactly rows older than now (5 s test margin); a `T/Z` row 1 s past the cutoff is deleted and 1 s inside survives; Plan 006's `deleted_ids` behavior stays intact; companion tests green.

## Out of Scope
- Maintenance-side guards/cutoffs (procedure `20261116-073054_01`), `get_typed` hardening (`_03`), `config.py` (`_04`), maintenance harness alignment and boundary tests (`_05`).
- `docs/41_db/db_06_api_and_operations-maintenance-and-rotation.md` update (plan Phase 3 step).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Store guards + cutoff rewrite + docstrings (plan Phase 2) | Completed | — | — | REQ-004, REQ-005; gated: plans/done/20261115-050112_dbreview006_maintenance-error-semantics.md phase all - re-read landed `deleted_ids` flow ; gate satisfied 2026-11-16: Plan 006 completed at HEAD d0500d87c (deleted_ids at store_impl.py:206, begin_immediate :189, tests at test_db_maintenance.py:1279+); anchors re-measured: delete_memories_before :177-207 (cutoffs :182/:192), collect_prunable_ids :209-216 (cutoff :213), memory_data_ops.py :134-155/:374 implementing store guards + T/Z cutoff rewrite (Plan 006 landed flow confirmed: deleted_ids :206, begin_immediate :189) verified 2026-11-16: targeted tests + gates green; full suite/diff-cover skipped per memo3 instruction |
| 2 | Companion tests in `tests/db/test_db_store_impl.py` (plan Phase 3) | Completed | — | — | REQ-007 (store part); companion harness days=30/7 tests confirmed present at :401-627 (2026-11-16) companion class TestMemoryDeleteStoreRetentionValidation (3 tests) landed; doc gap found during execution: 3 pre-existing SQL-format pinning assertions (:445/:476/:487 datetime('now', ?)) had to be re-pinned to the strftime T/Z form - intended REQ-004 contract change, not an assertion relaxation; radon delete_memories_before B(8) vs baseline B(7): guard adds 1 branch to an already-B(7) method, repo gate radon -n C passes; 38/38 green verified 2026-11-16: targeted tests + gates green; full suite/diff-cover skipped per memo3 instruction |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | verified 2026-11-16: targeted tests + gates green; full suite/diff-cover skipped per memo3 instruction |

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
- **Requirement ID**: REQ-004 (store cutoff rewrite), REQ-005 (negative-`older_than_days` guard), REQ-007 (companion store tests)
- **Source issue**: issues/20261114-092855_dbreview007_retention-input-validation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261115-050559_dbreview007_retention-input-validation.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261116-073054
- **Related target files**: `scripts/db/store_impl.py`, `tests/db/test_db_store_impl.py`
