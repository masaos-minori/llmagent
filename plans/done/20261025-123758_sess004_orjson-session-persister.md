# sess004 — Use orjson for JSON serialization in session_persister

**Source issue**: `issues/20261025-115739_sess004_orjson-session-persister.md`

> Path A (2 target files, behavior-preserving library swap). All 22 sections kept;
> some collapsed per the Path A rule. Verification (2026-10-25, all confirmed by
> reading current source): `session_persister.py` uses `import json` (~line 17),
> `json.loads(e["content"])` with `except (json.JSONDecodeError, KeyError)`
> (~lines 117-119), `content=json.dumps(summary)` (~line 161);
> `rules/coding.md:120` mandates orjson with the `config_loader.py`-only carve-out;
> the existing ast-grep gate (`rules/coding.md:77-78`) matches only `json.load($$$)`,
> confirming the gate-invisible claim; `diagnostic_store.py:15,82-83` already uses
> `orjson.loads` / `orjson.JSONDecodeError`.

## Goal

Bring `scripts/agent/session_persister.py` onto the repository's mandated `orjson`
serializer without changing the persisted payload semantics, so both writers of
`session_diagnostics.content` share one JSON implementation.

## Priority

Medium (issue-stated). Low-risk convention fix; currently enforcement-invisible
(ruff passes), so left uncorrected it silently diverges from every sibling writer.

## Scope

In scope:
- `scripts/agent/session_persister.py` — the three JSON call sites only.
- `tests/agent/test_session_persister.py` — round-trip test addition; any
  serialization-specific adjustments.

Out of scope (issue-stated):
- Repo-wide enforcement of the orjson rule (new ruff/ast-grep gate).
- `config_loader.py` (stdlib carve-out stands).
- Diagnostic/summary payload schema changes; function renames; persister restructuring.

## Background

`rules/coding.md:120`: "Use `orjson` (not stdlib `json`) for all JSON serialization —
`orjson.dumps()` returns `bytes`; call `.decode()` when a `str` is required". The
existing gate (`rules/coding.md:77-78`, ast-grep `json.load($$$)`) catches only
`json.load`, not `json.loads`/`json.dumps` — hence this file's violation was
enforcement-invisible. Measured runtime facts (orjson 3.11.9): default `orjson.dumps`
preserves dict insertion order and emits compact separators (stdlib emits
`", "`/`": "`), and `OPT_PRESERVE_ITERATION_DICT` no longer exists as an option.

## Problem

Three stdlib call sites in `session_persister.py` violate the rule and maintain a
second JSON implementation in the same persistence domain as `diagnostic_store.py`
(already orjson), creating divergence risk for future payload-format changes.

## Reason for Change

Verified violation with a confirmed mechanism of invisibility (gate pattern analysis).
Fixing now co-locates both `session_diagnostics.content` writers on one serializer.

## Implementation Intent

Same-call-site swap: `orjson.loads` for the parse, `orjson.dumps(summary).decode()`
for the summary write, exception clause adjusted to `orjson.JSONDecodeError` while
keeping the `KeyError` handling equivalent. No design change.

## Requirements

| ID | Requirement | Priority | Target |
|---|---|---|---|
| REQ-001 | No stdlib `json` import or call remains in `session_persister.py`. | must | scripts/agent/session_persister.py |
| REQ-002 | Parse site keeps equivalent exception semantics: `(orjson.JSONDecodeError, KeyError)` caught, payload skipped silently as today. | must | scripts/agent/session_persister.py |
| REQ-003 | Summary site writes `orjson.dumps(summary).decode()`; persisted document is semantically identical (same keys/values; insertion order preserved by orjson default). | must | scripts/agent/session_persister.py |
| REQ-004 | Round-trip test proves a persisted summary parses back to the same dict. | must | tests/agent/test_session_persister.py |
| REQ-005 | No other behavior change; existing persister tests pass (serialization-library-specific adjustments only if needed). | must | tests/agent/test_session_persister.py |

## Implementation Target Files

> One row per directly affected file.

| File | Action | Contract / Exports to Keep |
|---|---|---|
| scripts/agent/session_persister.py | modify | Module public API, function names, control flow, non-fatal failure semantics (warning + debug log), `DiagnosticStore` call shapes unchanged; only `import json` -> `import orjson` and the three call sites. |
| tests/agent/test_session_persister.py | modify | Existing assertions unchanged except serialization-specific adjustments; add round-trip test (REQ-004). |

## Reference Files

- `scripts/agent/diagnostic_store.py:15,82-83` — target orjson pattern (loads + JSONDecodeError).
- `rules/coding.md:77-78,120` — rule text and the gate's blind spot.
- `scripts/db/schema_sql.py:139-149` — `session_diagnostics.content` is TEXT; no format constraint.
- `docs/40_shared/shared_01_overview.md` (`orjson.dumps()` returns `bytes` constraint, cited by the issue).
- `docs/23_agent/agent_10_05_operations-and-observability-monitoring.md:61` — documented consumer reads summary via sqlite `json_extract` (key-order independent).

## Acceptance Criteria

| ID | Criterion | Maps to |
|---|---|---|
| AC-001 | `rg -n 'import json|json\.' scripts/agent/session_persister.py` returns nothing. | REQ-001 |
| AC-002 | `tests/agent/test_session_persister.py` passes; new round-trip test green (`loads(dumps(summary)) == summary`). | REQ-004, REQ-005 |
| AC-003 | Reader set green unmodified: `tests/agent/test_session_restore.py`, `tests/agent/test_agent_session.py`, `tests/agent/test_regression_diagnostic_persist.py`, `tests/agent/test_diagnostic_store.py`. | REQ-002, REQ-003 |
| AC-004 | `uv run ruff check` and `uv run mypy --no-namespace-packages` clean on the changed file. | REQ-001 |

## Tests

- Run existing `tests/agent/test_session_persister.py` (contains no stdlib-json
  expectations — verified by grep; expected to pass unchanged).
- Add: persist a session summary through the persister against the in-memory
  DiagnosticStore fixture already used in this file, read `content` back, parse with
  `orjson.loads`, assert equality with the expected summary dict (semantic
  round-trip, AC-002).
- Reader-set regression: run the session/export reader tests named in AC-003.

## Documentation Impact

N/A: behavior-preserving library swap; the rule already exists in `rules/coding.md`;
no documented payload format changes (issue Documentation Impact concurs).

## Assumptions

| Assumption | Confidence | Verification |
|---|---|---|
| No consumer compares the serialized summary byte-for-byte or depends on key order: the only Python reader is `session_persister.py` itself (`json.loads`-style dict parse, order-independent) and the only documented external reader is sqlite `json_extract` (order-independent). `OPT_SORT_KEYS` therefore not required; insertion order is preserved by orjson's default. | High | grep `session_summary` across scripts/tests/docs 2026-10-25: no byte-comparison found; orjson default order behavior measured on 3.11.9. Resolves the issue's Unresolved Question. |
| `orjson.JSONDecodeError` + `KeyError` catch is exception-semantics-equivalent to the current clause for all payloads that can reach the site. | High | Both JSONDecodeError classes subclass ValueError; the `KeyError` comes from `e["content"]` (dict access), unchanged by the serializer swap. |
| Separator difference (stdlib spaces vs orjson compact) is acceptable: no test or documented consumer asserts the exact bytes. | High | Test grep (AC-002 guards); docs read via `json_extract`. |

## Unknowns

| ID | Question | Confidence | Blocking | Verification Steps |
|---|---|---|---|---|
| U-001 | Any out-of-repo consumer (manual sqlite3 queries, external tooling) asserting exact summary bytes? | Low | No | Unverifiable from repo; repo-documented query (`agent_10_05:61`) uses `json_extract`, semantic-only. Accepted risk: semantic compatibility is the contract. |

## Affected areas

N/A: single module (`agent.session_persister`); `DiagnosticStore` and DB layers
untouched; `deploy.sh` impact: none. Payload bytes become compact (no separator
spaces) — semantic content identical; readers are dict-parsing or `json_extract`.

## Design

N/A beyond the swap itself (Path A, no design decision): mechanical replacement of
three call sites per `rules/coding.md:120` — `orjson.loads(e["content"])`,
`except (orjson.JSONDecodeError, KeyError)`, `content=orjson.dumps(summary).decode()`.
`OPT_SORT_KEYS` intentionally not used (Assumption 1); re-evaluate only if a
byte-stable export is ever specified.

## Implementation steps

1. Swap import + three call sites in `session_persister.py`.
2. Add round-trip test to `tests/agent/test_session_persister.py`.
3. Run targeted + reader-set validation (Validation plan), single commit.

## Validation plan

- Targeted: `uv run pytest tests/agent/test_session_persister.py tests/agent/test_diagnostic_store.py tests/agent/test_regression_diagnostic_persist.py -x -q`.
- Reader set: `uv run pytest tests/agent/test_session_restore.py tests/agent/test_agent_session.py -x -q` (issue Testing Expectations).
- Full: `uv run pytest tests/ -q` (baseline 10082 passed / 9 skipped) + `rules/toolchain.md` sequence; `lint-imports` 6 kept (`orjson` is a permitted third-party import, already used by sibling modules).
- Static: ruff + mypy on the changed file (issue Testing Expectations); AC-001 grep check.

## Adversarial Re-verification (2026-10-25, procedure generation)

- Call sites confirmed exactly at `session_persister.py:17` (`import json`), `:117`
  (`json.loads(e["content"])`), `:119` (`except (json.JSONDecodeError, KeyError)`),
  `:161` (`content=json.dumps(summary)`).
- Gate blind spot confirmed: `rules/coding.md:77-78` ast-grep pattern is
  `json.load($$$)` (matches only `json.load`); rule text at `:120` confirmed verbatim.
- orjson facts re-measured on the dev venv (orjson 3.11.9, `orjson>=3.10` in
  `pyproject.toml:12`): default `orjson.dumps` preserves insertion order and emits
  compact separators (`b'{"b":1,"a":2,...}'` vs stdlib `', '`/`': '`);
  `OPT_PRESERVE_ITERATION_DICT` does not exist.
- `test_session_persister.py` contains no stdlib-`json` usage (grep: zero `json`
  references); `DiagnosticStore()` + `db` fixture (line 63) is the in-memory pattern the
  round-trip test reuses.
- `agent_10_05:61` `json_extract` query confirmed; `shared_01_overview.md:117` holds the
  `orjson.dumps()` returns `bytes` constraint.
- Full-suite baseline figure "10082 passed / 9 skipped" is historical: collect-only
  reports 10091 tests at HEAD ad39f04f0.

## Risks

| Risk | Severity | Likelihood | Mitigation |
|---|---|---|---|
| Byte-level output changes (compact separators) break an undocumented external consumer. | Low | Low | Assumption recorded; semantic compatibility is the contract (issue Constraint); round-trip test pins semantics. |
| Payload containing types orjson cannot serialize (e.g. non-JSON-serializable values in summary) raises where stdlib also would have — but error text differs. | Low | Low | Summary dict is built from plain scalars/counts in this module (source read); non-fatal wrapper (`# noqa: BLE001` block) already contains persistence failures. |
| `orjson.loads` strictness (rejects some inputs stdlib tolerated, e.g. trailing data) on malformed stored rag payloads. | Low | Low | Rag payloads are written by `diagnostic_store` via orjson; malformed-row path already swallowed by the same except clause. |

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Swap import + three call sites (`session_persister.py`) | In Progress | — | — | re-verified against HEAD ad39f04f0 2026-10-25; exact lines 17/117/119/161 |
| 2 | Add round-trip test (`tests/agent/test_session_persister.py`) | In Progress | — | — | `REQ-004` |
| 3 | Targeted + reader-set validation, single commit | Pending | — | — | gate only; modifies no file |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261025-135131_01_scripts_agent_session_persister.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261025-135131_02_tests_agent_test_session_persister.py.md | 2 | Procedure | Pending | — | — |

## Traceability

- Implementation step 1 → REQ-001, REQ-002, REQ-003, REQ-005.
- Implementation step 2 → REQ-004 (AC-002).
- Implementation step 3 → AC-003, AC-004.

## Requirement Traceability

| Requirement | Test / Evidence | Acceptance Criterion |
|---|---|---|
| REQ-001 | rg check + ruff | AC-001, AC-004 |
| REQ-002 | Existing rag-parse tests in test_session_persister.py | AC-002, AC-003 |
| REQ-003 | Round-trip test + reader set | AC-002, AC-003 |
| REQ-004 | New round-trip test | AC-002 |
| REQ-005 | Unmodified existing suite runs | AC-002, AC-003 |
