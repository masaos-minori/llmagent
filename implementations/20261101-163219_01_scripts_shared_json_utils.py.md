## Goal

## Goal

Add the strict shared UTC ISO-8601 parser `parse_iso_utc(value)` to `scripts/shared/json_utils.py` that accepts exactly what `now_iso()` writes plus offsets and fractional seconds, and rejects naive strings (REQ-001 / AC-1).

## Scope

- Add `parse_iso_utc(value: str) -> datetime` returning a timezone-aware UTC `datetime`.
- Accept `YYYY-MM-DDTHH:MM:SSZ` (the production `now_iso()` format, `json_utils.py:45-51`), explicit offsets (`+09:00`-style, converted to UTC), and optional fractional seconds.
- Raise `ValueError` for naive strings (no `Z`/offset), malformed strings, and non-`str` input.
- No change to `now_iso` or `now_iso_raw` (Plan Scope Out-of-Scope: changing the output of `now_iso()`).

## Assumptions

- Plan `plans/20261030-114516_wflease001_stale-attempt-lease.md` is Frozen; its 18-row `Implementation Target Files` table (rows 17-18 added by the 2026-11-01 amendment) is the canonical scope and every target of this procedure is a row of that table.
- All baseline cites below were re-verified against branch `master` on 2026-11-01 (Plan Assumptions 'Re-verification record').
- Canonical semantics come from the Plan REQs (Plan `:37-46`): `parse_iso_utc` rejects naive input (REQ-001); no `mktime`/`strptime`/local time in recovery (REQ-002); unparseable timestamps are reported with distinct counts (REQ-003); nullable `owner_id`/`lease_expires_at` via a registered migration (REQ-004); owner and lease stamped at attempt start from the stage timeout plus a 30 s margin constant (REQ-005); staleness means lease expiry and `_STALE_GRACE_SEC` is removed (REQ-006); takeover is a conditional update requiring one row (REQ-007); legacy rows without a lease use the 3600 s age (REQ-008); tests use the production timestamp format (REQ-009); docs and ADR-001 INV-07 are amended (REQ-010).
- Owner decision (Plan UNK-02, 2026-10-30): deadline lease only — no heartbeat renewal, because `asyncio.wait_for` already bounds a normal stage.
- Ledger landing order (Plan UNK-06): `master` records code 2 / "1.2.0" (`migrations_workflow.py:42`); wftaskapi001 procedure 12 (`implementations/20261101-140834_12_scripts_db_migrations_workflow.py.md`, Pending) reserves the next slot. This Plan takes code 3 / "1.3.0" only if its step registers before wftaskapi001's, otherwise 4 / "1.4.0" (same rule as `implementations/20261101-145309_26_scripts_db_migrations_workflow.py.md`).
- Fencing dependency (Plan UNK-06): REQ-007's rejection of a late finish by the fenced owner lands with the wfrecovery001 conditional `finish_attempt` procedure (`implementations/20261101-145309_04_scripts_agent_workflow_attempt_ops.py.md`, Pending); at `master` `finish_attempt` is still unconditional (`attempt_ops.py:44-45`).
- The workflow timestamp format stays `YYYY-MM-DDTHH:MM:SSZ`; recovery round-trips it through `parse_iso_utc` unchanged (AC-1 test uses `now_iso()` output).

## Design decisions

- Implementation via `datetime.fromisoformat` after a single normalization: a trailing `Z` becomes `+00:00`; the result is `.astimezone(timezone.utc)` so the return value is always aware UTC.
- Naive input is rejected by checking `dt.tzinfo is None` after parsing — `fromisoformat` accepts naive strings silently, so the check is explicit (Plan Design 'Parser': a malformed row cannot be silently read as a local time).
- `ValueError` messages include the offending value and the reason (`naive`, `malformed`) so the recovery report (procedure 02) can log them verbatim.

## Alternatives considered

- (a) reuse the local `fromisoformat(...replace('Z','+00:00'))` in `scripts/agent/memory/scoring.py:25` — rejected: not reusable from `agent.workflow` without a cross-module import of an unrelated module, and it accepts naive input (Plan Design).
- (b) `dateutil`/third-party parser — rejected: stdlib-only project convention (`rules/coding.md`).

## Implementation
### Target file
`scripts/shared/json_utils.py`

### Procedure
1. Add `parse_iso_utc` after `now_iso_raw` (`json_utils.py:54-61`).
2. Normalize a trailing `Z` to `+00:00`, parse with `datetime.fromisoformat`, reject naive results, and return `.astimezone(timezone.utc)`.
3. Document the contract in the function docstring: accepted forms, rejection of naive input, and that it is the only ISO parser the workflow package may use.

### Method
Pure stdlib function in the existing shared module; no new imports beyond `datetime`/`timezone` already imported at `json_utils.py:1-20` region.

### Details
- Signature: `parse_iso_utc(value: str) -> datetime`.
- `json_utils` is layer `shared`; `agent.workflow` may import it — the import contract (`lint-imports`, baseline 6 kept) is unaffected.
- `fromisoformat` on Python 3.13 accepts `+00:00` offsets natively; the only normalization needed is the trailing-`Z` substitution.

## Compatibility considerations

- New function; no existing caller changes. `mcp_servers/file` consumers of `now_iso_raw` (`mtime` freshness code) are untouched.

## Security considerations

- All recovery/attempt SQL stays parameter-bound; owner and lease values are produced by the server (clock, host identity), never by caller-supplied strings.

## Rollback considerations

- Delete the function; no data or call-site to unwind because nothing imports it before procedures 02/09 land.

## Validation plan

- `uv run pytest tests/shared/test_json_utils.py -v` — new `TestParseIsoUtc` class (procedure 08) passes; all existing tests unchanged.
- Full sequence per `rules/toolchain.md`: `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `uv run python tools/check_module_size.py`.

## Completion criteria

- AC-1: `parse_iso_utc` returns the correct UTC instant for `Z`, `+09:00` offsets, and fractional seconds; raises `ValueError` for naive and malformed input; a test uses `now_iso()` output.

## Out of Scope

- Any change to `now_iso`/`now_iso_raw` output (Plan Out-of-Scope).
- The local `Z` parse in `scripts/agent/memory/scoring.py` (Plan Out-of-Scope; stays as is).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: Phase 1 (Timezone-safe parsing and conservative detection; independent)
- **Requirement ID**: `REQ-001`
- **Source issue**: issues/20261030-105723_wflease001_stale-attempt-lease.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-114516_wflease001_stale-attempt-lease.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261101-163219
- **Related target files**: `scripts/shared/json_utils.py`, `tests/shared/test_json_utils.py`, `scripts/agent/workflow/state_store.py`
