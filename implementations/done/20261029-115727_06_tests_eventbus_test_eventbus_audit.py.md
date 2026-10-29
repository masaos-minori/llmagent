## Goal

Add field-shape unit tests for the audit module (`REQ-003`, `REQ-005`, `REQ-007`; AC-2): the new `actor` key is present and equal to the passed value, all existing keys keep their current shape, successful records keep `error_type=""`, and the emitted JSON line contains no token substring.

## Scope

Create the new file `tests/eventbus/test_eventbus_audit.py`. No production code change here; the behavior under test is created by seq 01.

## Assumptions

- Source claims re-verified this cycle (2026-10-29): `tests/eventbus/test_eventbus_audit.py` does not exist (grep: no audit-module unit tests today); `log_privileged_action` emits through `logger.info` of an `orjson`-serialized dict with sorted keys; `_derive_token_fingerprint` at `auth.py:97` is `sha256(token).hexdigest()[:16]`.
- The caplog capture level must include INFO for the `eventbus.audit` logger.

## Design decisions

- Three tests (all new):
  - `test_privileged_record_has_actor_and_keeps_error_type_empty`: call `log_privileged_action(..., actor=_derive_token_fingerprint("unit-secret-token"))` under caplog, parse the captured line with `orjson.loads`, assert `actor` equals the passed fingerprint, `error_type == ""`, `outcome == "allowed"`, and the existing key set (`event`, `source`, `ts`, `consumer_id`, `request_id`, `route`, `target`) is unchanged.
  - `test_emitted_privileged_line_contains_no_token_substring`: with the raw secret `"unit-secret-token"` known, assert neither the raw token nor any longer prefix of it appears in the captured line; the fingerprint itself does appear.
  - `test_build_audit_record_shape_unchanged`: `_build_audit_record` outputs no `actor` key and keeps omitting empty `detail` (guards the seq 01 decision that auth-failure records stay byte-identical).
- Capture via the standard `caplog` fixture (`caplog.set_level(logging.INFO, logger="eventbus.audit")`); no caplog-handler patching.

## Alternatives considered

- Mock-based assertion instead of caplog: rejected; the Plan requires at least one test pinning the real emitted line shape (Risks: "mock-only audit tests never see the real JSON line").

## Implementation
### Target file

`tests/eventbus/test_eventbus_audit.py` (new file)

### Procedure

1. Create the file with `from __future__ import annotations`, imports: `logging`, `orjson`, `pytest`, `from eventbus.audit import _build_audit_record, log_privileged_action`, `from eventbus.auth import _derive_token_fingerprint`.
2. Implement the three tests above; each test reads the single captured record via `orjson.loads(caplog.records[-1].message)`.

### Method

New-file creation; plain function-style tests (no classes needed).

### Details

- Keep each test under ~25 lines; no fixtures beyond caplog; deterministic (no timestamps asserted beyond presence of the key).

## Compatibility considerations

- Pins the additive contract: future removal or renaming of `actor` fails these tests.

## Security considerations

- The test uses a clearly fake token constant and asserts it never appears in output — a direct regression guard for token leakage.

## Rollback considerations

- Test-only file: delete to roll back; must be removed together with the seq 01 feature revert.

## Validation plan

- `uv run pytest tests/eventbus/test_eventbus_audit.py -v`.
- `uv run ruff check tests/eventbus/test_eventbus_audit.py` and `uv run mypy tests/eventbus/test_eventbus_audit.py`.

## Completion criteria

- Three tests pass against the seq 01 implementation; the captured-line assertions observe the real JSON output.

## Out of Scope

- Route-level integration assertions (seq 07-09), doc updates (seq 10).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Aborted | — | — | Target file does not exist |
| 2 | Add or update tests per Validation plan | Aborted | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Aborted | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Aborted | — | — | |

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
- **Requirement ID**: REQ-003, REQ-005, REQ-007 (AC-2)
- **Source issue**: `issues/20261028-122415_ebaudit005_privileged-audit-actor-context.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261028-234417_ebaudit005_privileged-audit-actor-context.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261029-115727
- **Related target files**: tests/eventbus/test_eventbus_audit.py
