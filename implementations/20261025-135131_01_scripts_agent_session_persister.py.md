# Implementation Procedure — scripts/agent/session_persister.py

## Goal

Replace the three stdlib-`json` call sites with `orjson` so the module follows
`rules/coding.md:120` and shares one JSON implementation with `diagnostic_store.py`
(REQ-001..REQ-003, REQ-005).

## Scope

- Modify only `scripts/agent/session_persister.py`: the import line (17) and three
  call sites (117, 119, 161 — exact lines verified 2026-10-25 against HEAD ad39f04f0).
- No other file is modified by this procedure (round-trip test:
  `implementations/20261025-135131_02_tests_agent_test_session_persister.py.md`).

## Assumptions

- orjson 3.11.9 (dev venv; `orjson>=3.10` in `pyproject.toml:12`): default
  `orjson.dumps` preserves dict insertion order and emits compact separators
  (re-measured 2026-10-25); `OPT_PRESERVE_ITERATION_DICT (new)` does not exist.
- `orjson.JSONDecodeError` subclasses `ValueError` like `json.JSONDecodeError`; the
  `KeyError` half of the clause comes from `e["content"]` dict access and is untouched.
- No consumer compares summary bytes or depends on key order (plan Assumption 1;
  `agent_10_05:61` reads via sqlite `json_extract (new)` — verified).
- Compact-byte change is acceptable per the plan's semantic-compatibility contract.

## Design decisions

- Same-call-site swap, no design change (Path A): mechanical replacement per
  `rules/coding.md:120` — `orjson.loads`, `orjson.JSONDecodeError`,
  `orjson.dumps(summary).decode()`.
- `OPT_SORT_KEYS` intentionally NOT used: nothing requires byte-stable output;
  re-evaluate only if a byte-stable export is ever specified (plan Design).
- Silent-skip semantics preserved exactly: the rag-parse `except` clause keeps
  `pass`, the summary write stays inside the existing non-fatal
  `(RuntimeError, sqlite3.Error)` containment.

## Alternatives considered

- Adding an ast-grep/ruff gate for `json.loads`/`json.dumps` now: rejected — repo-wide
  enforcement is issue out-of-scope (separate concern).
- Keeping stdlib `json` in the parse site only: rejected — REQ-001 requires zero stdlib
  `json` in the file.

## Implementation
### Target file
`scripts/agent/session_persister.py`

### Procedure

Swap the import and the three call sites.

### Method
Line 17, from:

```python
import json
```

to:

```python
import orjson
```

Line 117: `diag = json.loads(e["content"])` ->
`diag = orjson.loads(e["content"])`.

Line 119: `except (json.JSONDecodeError, KeyError):` ->
`except (orjson.JSONDecodeError, KeyError):`.

Line 161: `content=json.dumps(summary),` ->
`content=orjson.dumps(summary).decode(),`.

### Details
- Import placement must keep ruff's import ordering (orjson is third-party, same block
  position as the removed stdlib `json`; check against the file's existing import
  layout).
- Module public API, function names, control flow, warning/debug containment, and
  `DiagnosticStore` call shapes unchanged (target-table contract).
- AC-001 check after the edit: `rg -n 'import json|json\.' scripts/agent/session_persister.py`
  returns nothing.

## Compatibility considerations

- Persisted payload bytes become compact (no `", "`/`": "` separators); readers parse
  as dicts (`orjson.loads` in `diagnostic_store.py:82`) or via sqlite `json_extract (new)`
  (order-independent) — verified.
- Existing rag-parse tests in `tests/agent/test_session_persister.py` contain no
  stdlib-json expectations (grep verified: zero `json` references) — expected to pass
  unchanged.
- orjson strictness (e.g. trailing data) on malformed stored payloads: payloads are
  written by `diagnostic_store` via orjson; malformed rows are already swallowed by the
  same except clause (plan Risk 3).

## Security considerations

N/A: serializer swap only; no new input surface, no schema change
(`session_diagnostics.content` is TEXT with no format constraint,
`schema_sql.py:139-149` verified).

## Rollback considerations

Revert the single commit; four lines, no data migration (rows written in compact form
remain readable by any JSON parser).

## Validation plan

- Targeted (plan Validation): `uv run pytest tests/agent/test_session_persister.py
  tests/agent/test_diagnostic_store.py tests/agent/test_regression_diagnostic_persist.py -x -q`.
- Reader set: `uv run pytest tests/agent/test_session_restore.py
  tests/agent/test_agent_session.py -x -q`.
- Full: `uv run pytest tests/ -q` (10091 collected at HEAD ad39f04f0; plan's "10082
  passed" is historical) + `rules/toolchain.md`; `lint-imports` 6 kept (orjson is a
  permitted third-party import already used by siblings).
- Static: `uv run ruff check` + `uv run mypy --no-namespace-packages` on the changed
  file; AC-001 grep check.

## Completion criteria

- AC-001: no stdlib `json` import or call remains in the file.
- AC-002/AC-003: persister suite and reader set green (round-trip test from procedure
  02 green).
- AC-004: ruff + mypy clean on the changed file.

## Out of Scope

- The round-trip test (procedure 02).
- Repo-wide orjson enforcement gate (issue out-of-scope).
- `config_loader.py` (stdlib carve-out stands).
- Payload schema changes or persister restructuring.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Swap import + three call sites (17, 117, 119, 161) | Pending | — | — | |
| 2 | Run targeted + reader-set validation | Pending | — | — | round-trip test lands via procedure 02 |
| 3 | Run AC-001 grep check + ruff/mypy | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-005
- **Source issue**: `issues/done/20261025-115739_sess004_orjson-session-persister.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-123758_sess004_orjson-session-persister.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261025-135131
- **Related target files**: scripts/agent/session_persister.py
