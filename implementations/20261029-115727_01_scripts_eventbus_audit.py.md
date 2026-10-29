## Goal

Add the `actor` field to privileged-action audit records and document the success `error_type=""` convention in `scripts/eventbus/audit.py` (`REQ-002`, `REQ-003`, `REQ-007`): `log_privileged_action` gains an `actor` parameter emitted as a new record key, and the module docstring records that successful privileged records carry `error_type=""`.

## Scope

Modify `scripts/eventbus/audit.py` only: the module docstring, the `AuditRecord` TypedDict, and `log_privileged_action`. `_build_audit_record` and `log_auth_failure` are not touched. The call-site changes are seq 02-05; the tests are seq 06-09.

## Assumptions

- Source claims re-verified this cycle (2026-10-29): `AuditRecord` is a `TypedDict` at `audit.py:45-57` with `error_type: str` (line 56) and `detail: NotRequired[str]`; `_build_audit_record` is at `:60` with `error_type: str = ""` (line 67) and always emits the `error_type` key (line 91), omitting only empty `detail`; `log_privileged_action` is a sync function at `:129-166` with no `error_type` parameter and hardcodes `error_type=""` (line 152). No `actor` field exists anywhere in the module.
- UNK-01 was resolved by the owner on 2026-10-29: keep the current `error_type=""` shape; only the module docstring gains the convention note. UNK-02 resolved: `actor` is the acting `Principal.token_fingerprint` value, carried here as a plain string parameter (this module does not import `Principal`).
- Records are emitted as one `orjson`-serialized JSON line through the module logger (`logger.info`, sorted keys); there is no DB storage (grep 2026-10-29 found no audit table in `scripts/eventbus/db.py` or `migrations.py`).

## Design decisions

- `actor` is a keyword parameter with default `""` on `log_privileged_action` and is written into the record after `_build_audit_record` returns; `_build_audit_record` stays unchanged so `log_auth_failure` records keep their exact current shape (additive-change constraint REQ-007).
- `AuditRecord` gains `actor: NotRequired[str]` so the new key is typed without forcing it onto auth-failure records.
- The module docstring's `error_type` vocabulary note (line 12) gains an explicit sentence that successful privileged records carry `error_type=""`.

## Alternatives considered

- Adding `actor` to `_build_audit_record` instead: rejected; it would invite the key into `log_auth_failure` records, which the Plan keeps out of scope.
- Omitting the `actor` key when empty: rejected for privileged records -- the three privileged call sites always pass a fingerprint, and the shape tests (seq 06) pin the key as always present for privileged records.

## Implementation
### Target file

`scripts/eventbus/audit.py`

### Procedure

1. Extend the module docstring `error_type` note (line 12 region) with: successful privileged-action records carry `error_type=""`.
2. Add `actor: NotRequired[str]` to the `AuditRecord` TypedDict (after `detail`).
3. Change the signature to `def log_privileged_action(consumer_id: str, request_id: str, route: str, target: str, detail: str = "", actor: str = "") -> None:` and document the new Args entry.
4. After `record = _build_audit_record(...)`, set `record["actor"] = actor` before the `logger.info(orjson.dumps(...))` emission.

### Method

Direct edit; no new module, no new import (`NotRequired` is already imported at `audit.py:37`).

### Details

- The emission line and `orjson.OPT_SORT_KEYS` option stay unchanged; the new key appears sorted like the others.
- Keep all existing field names and values byte-identical (REQ-007).

## Compatibility considerations

- Additive JSON key: downstream log parsers that ignore unknown keys are unaffected; `log_auth_failure` records are byte-identical. No shape change to `error_type` (UNK-01 resolved decision).

## Security considerations

- The `actor` value is a non-secret SHA-256 prefix (16 hex chars) derived by `scripts/eventbus/auth.py::_derive_token_fingerprint`; this module never receives or logs a raw token. Tests in seq 06 assert no token substring in the emitted line.

## Rollback considerations

- Reverting this file restores the previous record shape; `actor` is a single added key and parameter with no dependent readers at write time (call sites land in seq 02-05 and simply pass an extra kwarg).

## Validation plan

- `uv run pytest tests/eventbus/test_eventbus_audit.py` (seq 06 tests): new key present and equal to the passed value; all existing keys unchanged; `error_type=""` on success; one JSON line; no token substring (caplog).
- `uv run ruff check scripts/eventbus/audit.py` and `uv run mypy scripts/eventbus/audit.py`.

## Completion criteria

- `log_privileged_action` accepts `actor` and emits it; `AuditRecord` types it; the docstring states the success `error_type` convention; seq 06 tests pass; static gates clean.

## Out of Scope

- `_build_audit_record`, `log_auth_failure`, record storage/rotation, doc rows in `docs/24_eventbus/eventbus_08_reference_api.md` (seq 10).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | Tests are seq 06; land after this row |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Doc rows are seq 10 |

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
- **Requirement ID**: REQ-002, REQ-003, REQ-007 (AC-1, AC-2)
- **Source issue**: `issues/20261028-122415_ebaudit005_privileged-audit-actor-context.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261028-234417_ebaudit005_privileged-audit-actor-context.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261029-115727
- **Related target files**: scripts/eventbus/audit.py
