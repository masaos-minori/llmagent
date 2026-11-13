## Goal

Remove `topic_authorization` pairs from the principal map, replace tolerant `getattr`/`hasattr` config reads with direct attribute reads, delete the dead `_CONSUMER_ID_ALLOWLIST`, remove the `Precedent`/`REQ-003` comments, and use the `audit.py` error-type constants (REQ-002, REQ-003, REQ-005, REQ-006).

## Scope
**Release unit**: single-authorization-format (with rows 01, 04, 05, 06, 07, 14, 17); the `error_type` constants part belongs to the authorization-audit-record release unit (with rows 03, 04, 05, 14), per the Plan's phase mapping (row 02 spans steps 2, 4, 5)

## Assumptions
- `_ROUTE_ROLE_MAP` (line 75) stays: `tools/generate_reference_table.py:572-574` reads it by AST (UNK-02).
- The `error_type` values are unchanged strings, so existing log queries and tests keep working.

## Design decisions
- Direct attribute reads: `config` is an `EventBusConfig` instance whose fields all exist; tolerant reads hide misspelled or missing fields (REQ-003).

## Alternatives considered
- Deleting `_ROUTE_ROLE_MAP` too: rejected; it would break the reference generator (Plan Risk row; UNK-02).

## Implementation
### Target file
`scripts/eventbus/auth.py`
### Procedure
Remove the topic-side pairs, harden the config reads, delete the dead table and stale comments, and switch audit literals to constants.
### Method
In-place edits inside `_build_principal_map`, the middleware, and the token helpers; one new import from `eventbus.audit` (same package, no contract change).
### Details
- Delete the `topic_authorization` read (186) and the pair-expansion loop (200-201); keep the `consumer_authorization` expansion (185, 197-199) as the only source of consumer pairs. Verified 2026-11-13: the comment block at 181-184 names `topic_authorization` and must be reworded to name only `consumer_authorization` (otherwise the AC-2/AC-3 searches fail on this file); reword the "Both mappings empty" comment at 195-196 to describe the single mapping.
- Replace `getattr(config, field, None)` at 156, 185, 188, 207, 217, 270 and `hasattr(config, "auth_token")` at 174 with direct `config.<field>` reads (REQ-003).
- Delete `_CONSUMER_ID_ALLOWLIST` (90); `rg` confirms zero references.
- Keep `_ROUTE_ROLE_MAP` (75) unchanged.
- Delete the `Precedent` comments (22-23) and the `(REQ-003)` label in the duplicate-token guard comment (144) (REQ-006).
- Import the constants added by row 03 and replace the literals at 312 (`authentication_failed`), 349 (`authorization_failed`), 381 and 399 (`consumer_identity_rejected`), 421 (`topic_authorization_rejected`) with the constant names (REQ-005); the emitted strings are unchanged. This bullet is part B of this row and runs in the authorization-audit-record unit, after row 03 adds the constants; the literals stay in the single-authorization-format unit (Plan: constants land in Phase 5).

## Compatibility considerations
- Row 14 (`test_eventbus_auth.py`) drops the `topic_authorization=` fixture arguments in the same unit.

## Security considerations
- Strict reads make a missing or misspelled config field fail at import/build time instead of silently yielding `None` in the module that enforces authorization.

## Rollback considerations
- Reverting the file restores tolerant reads and the literals; no persisted state changes.

## Validation plan
- `uv run pytest tests/eventbus/test_eventbus_auth.py tests/eventbus/test_eventbus_consumer_authorization.py`
- AC-3 acceptance search: `rg -n "getattr\(config|hasattr\(config|_CONSUMER_ID_ALLOWLIST|topic_authorization" scripts/eventbus/auth.py` returns nothing (the pair name may appear only as the audit error-type value via the constant).
- AC-6: `rg -n "Precedent|Mirrors scripts/|REQ-[0-9]+" scripts/eventbus/auth.py` returns nothing.

## Completion criteria
- REQ-003 and REQ-005 states hold in this file; AC-3 and AC-6 searches are clean for it.

## Out of Scope
- `_ROUTE_ROLE_MAP` removal (UNK-02).
- `getattr` reads in `subscribe_route.py` and `app.py` (Plan Assumptions).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-11-13 | 2026-11-13 | — |
| 2 | Add or update tests per Validation plan | Completed | 2026-11-13 | 2026-11-13 | — |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-13 | 2026-11-13 | unit-2 targeted+full suites green; diff-cover 100% |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 2026-11-13 | 2026-11-13 | — |

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
- **Requirement ID**: REQ-002, REQ-003, REQ-005, REQ-006
- **Source issue**: issues/done/20261110-170832_rmcompat004_eventbus-config-auth-audit.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-120726_rmcompat004_eventbus-config-auth-audit.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261113-135237
- **Related target files**: `scripts/eventbus/auth.py`
